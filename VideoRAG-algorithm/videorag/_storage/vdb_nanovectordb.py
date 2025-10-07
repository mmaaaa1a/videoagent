import asyncio
import os
import torch
from dataclasses import dataclass
import numpy as np
from nano_vectordb import NanoVectorDB
from tqdm import tqdm
from imagebind.models import imagebind_model
from imagebind.models.imagebind_model import ImageBindModel

from .._utils import logger
from ..base import BaseVectorStorage


def get_imagebind_model() -> ImageBindModel:
    """获取ImageBind模型，优先使用本地模型文件"""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # 1. 首先尝试从环境变量配置的路径加载
    model_path = os.getenv('IMAGEBIND_MODEL_PATH', '/app/models')
    local_model_file = os.path.join(model_path, 'imagebind.pth')

    if os.path.exists(local_model_file):
        try:
            logger.info(f"🔄 从本地加载ImageBind模型: {local_model_file}")
            embedder = ImageBindModel(
                vision_embed_dim=1280,
                vision_num_blocks=32,
                vision_num_heads=16,
                text_embed_dim=1024,
                text_num_blocks=24,
                text_num_heads=16,
                out_embed_dim=1024,
                audio_drop_path=0.1,
                imu_drop_path=0.7,
            )
            embedder.load_state_dict(torch.load(local_model_file, map_location=device))
            embedder = embedder.to(device)
            embedder.eval()
            logger.info(f"✅ 本地ImageBind模型加载成功，设备: {device}")
            return embedder
        except Exception as e:
            logger.warning(f"⚠️ 本地模型加载失败: {e}，尝试在线下载")

    # 2. 如果本地模型不存在或加载失败，使用默认下载方式
    logger.info("🌐 使用在线方式下载ImageBind模型...")
    try:
        embedder = imagebind_model.imagebind_huge(pretrained=True)
        embedder = embedder.to(device)
        embedder.eval()
        logger.info(f"✅ 在线ImageBind模型加载成功，设备: {device}")
        return embedder
    except Exception as e:
        logger.error(f"❌ ImageBind模型加载失败: {e}")
        raise


@dataclass
class NanoVectorDBStorage(BaseVectorStorage):
    cosine_better_than_threshold: float = 0.2
    
    def __post_init__(self):

        self._client_file_name = os.path.join(
            self.global_config["working_dir"], f"vdb_{self.namespace}.json"
        )
        self._max_batch_size = self.global_config["llm"]["embedding_batch_num"]
        self._client = NanoVectorDB(
            self.embedding_func.embedding_dim, storage_file=self._client_file_name
        )
        self.cosine_better_than_threshold = self.global_config.get(
            "query_better_than_threshold", self.cosine_better_than_threshold
        )

    async def upsert(self, data: dict[str, dict]):
        logger.info(f"Inserting {len(data)} vectors to {self.namespace}")
        if not len(data):
            logger.warning("You insert an empty data to vector DB")
            return []
        list_data = [
            {
                "__id__": k,
                **{k1: v1 for k1, v1 in v.items() if k1 in self.meta_fields},
            }
            for k, v in data.items()
        ]
        contents = [v["content"] for v in data.values()]
        batches = [
            contents[i : i + self._max_batch_size]
            for i in range(0, len(contents), self._max_batch_size)
        ]
        embeddings_list = await asyncio.gather(
            *[self.embedding_func(batch) for batch in batches]
        )
        embeddings = np.concatenate(embeddings_list)
        for i, d in enumerate(list_data):
            d["__vector__"] = embeddings[i]
        results = self._client.upsert(datas=list_data)
        return results

    async def query(self, query: str, top_k=5):
        embedding = await self.embedding_func([query])
        embedding = embedding[0]
        results = self._client.query(
            query=embedding,
            top_k=top_k,
            better_than_threshold=self.cosine_better_than_threshold,
        )
        results = [
            {**dp, "id": dp["__id__"], "distance": dp["__metrics__"]} for dp in results
        ]
        return results

    async def index_done_callback(self):
        self._client.save()


@dataclass
class NanoVectorDBVideoSegmentStorage(BaseVectorStorage):
    embedding_func = None
    segment_retrieval_top_k: float = 2
    
    def __post_init__(self):
        
        self._client_file_name = os.path.join(
            self.global_config["working_dir"], f"vdb_{self.namespace}.json"
        )
        self._max_batch_size = self.global_config["video_embedding_batch_num"]
        self._client = NanoVectorDB(
            self.global_config["video_embedding_dim"], storage_file=self._client_file_name
        )
        self.top_k = self.global_config.get(
            "segment_retrieval_top_k", self.segment_retrieval_top_k
        )
    
    async def upsert(self, video_name, segment_index2name, video_output_format):
        embedder = get_imagebind_model()
        
        logger.info(f"Inserting {len(segment_index2name)} segments to {self.namespace}")
        if not len(segment_index2name):
            logger.warning("You insert an empty data to vector DB")
            return []
        list_data, video_paths = [], []
        cache_path = os.path.join(self.global_config["working_dir"], '_cache', video_name)
        index_list = list(segment_index2name.keys())
        for index in index_list:
            list_data.append({
                "__id__": f"{video_name}_{index}",
                "__video_name__": video_name,
                "__index__": index,
            })
            segment_name = segment_index2name[index]
            video_file = os.path.join(cache_path, f"{segment_name}.{video_output_format}")
            video_paths.append(video_file)
        batches = [
            video_paths[i: i + self._max_batch_size]
            for i in range(0, len(video_paths), self._max_batch_size)
        ]
        # 延迟导入以避免循环依赖
        from .._videoutil import encode_video_segments

        embeddings = []
        for _batch in tqdm(batches, desc=f"Encoding Video Segments {video_name}"):
            batch_embeddings = encode_video_segments(_batch, embedder)
            embeddings.append(batch_embeddings)
        embeddings = torch.concat(embeddings, dim=0)
        embeddings = embeddings.numpy()
        for i, d in enumerate(list_data):
            d["__vector__"] = embeddings[i]
        results = self._client.upsert(datas=list_data)
        return results
    
    async def query(self, query: str):
        # 延迟导入以避免循环依赖
        from .._videoutil import encode_string_query

        embedder = get_imagebind_model()

        embedding = encode_string_query(query, embedder)
        embedding = embedding[0]
        results = self._client.query(
            query=embedding,
            top_k=self.top_k,
            better_than_threshold=-1,
        )
        results = [
            {**dp, "id": dp["__id__"], "distance": dp["__metrics__"]} for dp in results
        ]
        return results
    
    async def index_done_callback(self):
        self._client.save()
