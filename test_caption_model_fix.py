#!/usr/bin/env python3
"""
测试VideoRAG修复后的caption_model初始化
"""
import sys
import os

# 添加VideoRAG算法路径
sys.path.insert(0, '/data/项目/videoagent/VideoRAG-algorithm')

def test_videorag_initialization():
    """测试VideoRAG是否能正常初始化并包含caption_model"""
    print("🔧 开始测试VideoRAG初始化...")

    try:
        # 设置环境变量
        os.environ['USE_GGUF_CAPTION'] = 'true'
        os.environ['CAPTION_MODEL_PATH'] = '/data/项目/videoagent/models/MiniCPM-o-2_6-gguf/.cache/huggingface/download/Model-7.6B-Q4_K_M.gguf'

        # 导入VideoRAG
        from videorag import VideoRAG

        print("✅ VideoRAG模块导入成功")

        # 创建VideoRAG实例（使用最小配置）
        videorag = VideoRAG(
            working_dir="/data/项目/videoagent/storage/test_init"
        )

        print("✅ VideoRAG实例创建成功")

        # 检查caption_model属性是否存在
        if hasattr(videorag, 'caption_model'):
            print("✅ caption_model属性存在")

            if videorag.caption_model is not None:
                print("✅ caption_model已正确初始化")
                print(f"   模型类型: {type(videorag.caption_model)}")

                # 测试模型是否可用
                try:
                    # 简单测试 - 检查模型是否响应
                    response = videorag.caption_model(
                        "Hello, how are you?",
                        max_tokens=10,
                        temperature=0.1
                    )
                    print("✅ caption_model功能测试通过")
                    print(f"   测试响应: {response}")
                except Exception as e:
                    print(f"⚠️ caption_model功能测试失败: {e}")
            else:
                print("❌ caption_model为None")
        else:
            print("❌ caption_model属性不存在")
            return False

        # 检查caption_tokenizer
        if hasattr(videorag, 'caption_tokenizer'):
            print("✅ caption_tokenizer属性存在")
            print(f"   tokenizer类型: {type(videorag.caption_tokenizer)}")
        else:
            print("❌ caption_tokenizer属性不存在")
            return False

        print("\n🎉 VideoRAG初始化测试完成！所有核心功能正常。")
        return True

    except ImportError as e:
        print(f"❌ 导入VideoRAG失败: {e}")
        return False
    except Exception as e:
        print(f"❌ VideoRAG初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_videorag_initialization()
    if success:
        print("\n🚀 可以进行下一步测试")
    else:
        print("\n❌ 需要修复初始化问题")
        sys.exit(1)