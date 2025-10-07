#!/usr/bin/env python3
"""
简化测试VideoRAG修复后的caption_model初始化
"""
import sys
import os

# 添加VideoRAG算法路径
sys.path.insert(0, '/data/项目/videoagent/VideoRAG-algorithm')

def test_caption_model_only():
    """仅测试caption_model的加载功能"""
    print("🔧 开始测试caption_model加载...")

    try:
        # 设置环境变量
        os.environ['USE_GGUF_CAPTION'] = 'true'
        os.environ['CAPTION_MODEL_PATH'] = '/data/项目/videoagent/models/MiniCPM-o-2_6-gguf/.cache/huggingface/download/Model-7.6B-Q4_K_M.gguf'

        print("✅ 环境变量设置完成")

        # 导入LLMConfig
        from videorag._llm import openai_config

        print("✅ LLMConfig导入成功")

        # 创建一个最小的VideoRAG类来测试caption_model加载
        from dataclasses import dataclass, field

        @dataclass
        class TestVideoRAG:
            working_dir: str = "./storage/test"

            def load_caption_model(self, debug=False):
                # 这是VideoRAG中的load_caption_model方法的核心代码
                if not debug:
                    use_gguf = os.getenv('USE_GGUF_CAPTION', 'false').lower() == 'true'

                    if use_gguf:
                        # 使用GGUF模型
                        from llama_cpp import Llama
                        model_path = os.getenv('CAPTION_MODEL_PATH', '/data/项目/videoagent/models/MiniCPM-o-2_6-gguf/.cache/huggingface/download/Model-7.6B-Q4_K_M.gguf')
                        self.caption_model = Llama(
                            model_path=model_path,
                            n_ctx=int(os.getenv('GGUF_CONTEXT_SIZE', '4096')),
                            n_gpu_layers=0,
                            n_threads=int(os.getenv('GGUF_N_THREADS', '32')),
                            verbose=False,
                            n_batch=int(os.getenv('GGUF_BATCH_SIZE', '64'))
                        )
                        self.caption_tokenizer = None  # GGUF不需要tokenizer
                    else:
                        # 使用原有MiniCPM-V模型
                        from transformers import AutoModel, AutoTokenizer
                        self.caption_model = AutoModel.from_pretrained('./MiniCPM-V-2_6-int4', trust_remote_code=True)
                        self.caption_tokenizer = AutoTokenizer.from_pretrained('./MiniCPM-V-2_6-int4', trust_remote_code=True)
                        self.caption_model.eval()
                else:
                    self.caption_model = None
                    self.caption_tokenizer = None

        print("✅ 测试类创建成功")

        # 测试caption_model加载
        test_videorag = TestVideoRAG()
        test_videorag.load_caption_model()

        print("✅ caption_model加载完成")

        # 检查结果
        if hasattr(test_videorag, 'caption_model') and test_videorag.caption_model is not None:
            print("✅ caption_model属性存在且不为None")
            print(f"   模型类型: {type(test_videorag.caption_model)}")

            # 简单测试
            try:
                response = test_videorag.caption_model(
                    "Hello, how are you?",
                    max_tokens=10,
                    temperature=0.1
                )
                print("✅ caption_model功能测试通过")
                print(f"   测试响应: {response}")
                return True
            except Exception as e:
                print(f"⚠️ caption_model功能测试失败: {e}")
                return False
        else:
            print("❌ caption_model属性不存在或为None")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_videorag_with_existing_config():
    """使用现有配置测试VideoRAG"""
    print("\n🔧 开始测试VideoRAG现有配置...")

    try:
        # 导入VideoRAG
        from videorag import VideoRAG
        print("✅ VideoRAG模块导入成功")

        # 设置环境变量（使用项目中的配置）
        os.environ['OPENAI_API_KEY'] = 'sk-test-key'
        os.environ['OPENAI_BASE_URL'] = 'https://api.openai.com/v1'
        os.environ['ALI_DASHSCOPE_API_KEY'] = 'sk-test-key'
        os.environ['ALI_DASHSCOPE_BASE_URL'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

        # 创建VideoRAG实例
        videorag = VideoRAG(
            working_dir="/data/项目/videoagent/storage/test_caption_fix"
        )

        print("✅ VideoRAG实例创建成功")

        # 检查caption_model
        if hasattr(videorag, 'caption_model') and videorag.caption_model is not None:
            print("✅ VideoRAG.caption_model已正确初始化")
            print(f"   模型类型: {type(videorag.caption_model)}")
            return True
        else:
            print("❌ VideoRAG.caption_model未正确初始化")
            return False

    except Exception as e:
        print(f"❌ VideoRAG测试失败: {e}")
        # 不打印完整traceback以避免干扰
        return False

if __name__ == "__main__":
    print("🚀 开始caption_model修复验证测试\n")

    # 测试1：基础功能测试
    success1 = test_caption_model_only()

    # 测试2：VideoRAG集成测试
    success2 = test_videorag_with_existing_config()

    print(f"\n📊 测试结果:")
    print(f"   基础功能测试: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"   VideoRAG集成测试: {'✅ 通过' if success2 else '❌ 失败'}")

    if success1 and success2:
        print("\n🎉 所有测试通过！caption_model修复成功。")
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查。")