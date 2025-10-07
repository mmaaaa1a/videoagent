from huggingface_hub import snapshot_download
import os
# 设置下载目录                                                                                                                                                                                                                                                                                                                                                                                        │ │
model_dir = "/data/项目/videoagent/models/MiniCPM-V-2_6-int4"
# 下载模型                                                                                                                                                                                                                                                                                                                                                                                            │ │
snapshot_download(repo_id="openbmb/MiniCPM-V-2_6-int4",local_dir=model_dir,local_dir_use_symlinks=False)

print(f"模型已下载到: {model_dir}")   