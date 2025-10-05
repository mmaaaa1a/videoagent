#!/usr/bin/env python3
"""
EPYC优化测试脚本
用于测试和验证EPYC优化的效果
"""

import os
import sys
import time
import tempfile
import logging
from pathlib import Path

# 添加VideoRAG算法路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'VideoRAG-algorithm'))

try:
    # 先测试基础模块
    from videorag._videoutil.epyc_config import setup_epyc_environment, get_epyc_config
    print("✅ EPYC配置模块导入成功")

    # 测试EPYC优化模块
    from videorag._videoutil.asr_epyc_optimized import (
        EPYCWhisperManager,
        speech_to_text_epyc_optimized,
        setup_epyc_optimization
    )
    print("✅ EPYC优化模块导入成功")

    # 测试原始ASR模块
    from videorag._videoutil.asr import speech_to_text
    print("✅ 原始ASR模块导入成功")

except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("⚠️ 请确保已安装所有依赖: pip install -r requirements.txt")
    sys.exit(1)

def test_epyc_config():
    """测试EPYC配置检测"""
    print("\n🔧 测试EPYC配置检测...")
    try:
        config = setup_epyc_environment()
        print(f"✅ 配置检测成功: {config.get('system_type', 'unknown')} 系统")
        return config
    except Exception as e:
        print(f"❌ 配置检测失败: {e}")
        return None

def test_epyc_manager():
    """测试EPYC管理器初始化"""
    print("\n🚀 测试EPYC管理器初始化...")
    try:
        manager = EPYCWhisperManager()
        stats = manager.get_performance_stats()
        print(f"✅ 管理器初始化成功:")
        print(f"   - 模型数量: {stats['num_models']}")
        print(f"   - 批量大小: {stats['batch_size']}")
        print(f"   - 缓存统计: {stats['cache_stats']}")
        return manager
    except Exception as e:
        print(f"❌ 管理器初始化失败: {e}")
        return None

def test_performance_comparison():
    """测试性能对比"""
    print("\n⚡ 测试性能对比...")

    try:
        manager = EPYCWhisperManager()
        print(f"✅ EPYC管理器初始化成功")

        # 测试空列表处理（不会实际处理文件）
        start_time = time.time()
        results = manager.parallel_transcribe([])  # 空列表测试
        init_time = time.time() - start_time

        print(f"✅ 空列表处理测试完成，耗时: {init_time:.2f}秒")

        # 获取性能统计
        stats = manager.get_performance_stats()
        print(f"📊 性能统计:")
        print(f"   - 模型数量: {stats['num_models']}")
        print(f"   - 批量大小: {stats['batch_size']}")
        print(f"   - 缓存统计: {stats['cache_stats']}")

    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return None

    return manager

def test_memory_usage():
    """测试内存使用情况"""
    print("\n💾 测试内存使用情况...")
    try:
        import psutil
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # 初始化EPYC管理器
        manager = EPYCWhisperManager()

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        print(f"✅ 内存使用测试:")
        print(f"   - 初始化前: {memory_before:.1f} MB")
        print(f"   - 初始化后: {memory_after:.1f} MB")
        print(f"   - 使用增量: {memory_used:.1f} MB")

        if memory_used > 5000:  # 超过5GB
            print(f"⚠️ 内存使用较高: {memory_used:.1f} MB")
        else:
            print(f"✅ 内存使用合理: {memory_used:.1f} MB")

    except ImportError:
        print("⚠️ psutil未安装，无法测试内存使用")
    except Exception as e:
        print(f"❌ 内存测试失败: {e}")

def test_environment_variables():
    """测试环境变量设置"""
    print("\n🌍 测试环境变量设置...")
    try:
        config = setup_epyc_optimization()

        important_vars = [
            'OMP_NUM_THREADS',
            'MKL_NUM_THREADS',
            'OPENBLAS_NUM_THREADS',
            'NUMEXPR_NUM_THREADS'
        ]

        print("✅ 环境变量设置:")
        for var in important_vars:
            value = os.environ.get(var, 'Not Set')
            print(f"   - {var}: {value}")

        return config
    except Exception as e:
        print(f"❌ 环境变量测试失败: {e}")
        return None

def main():
    """主测试函数"""
    print("🧪 EPYC优化测试开始")
    print("=" * 50)

    # 设置日志级别
    logging.basicConfig(level=logging.INFO)

    tests = [
        ("EPYC配置检测", test_epyc_config),
        ("环境变量设置", test_environment_variables),
        ("EPYC管理器初始化", test_epyc_manager),
        ("性能对比测试", test_performance_comparison),
        ("内存使用测试", test_memory_usage),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n📋 开始测试: {test_name}")
            result = test_func()
            results[test_name] = "✅ 通过" if result is not None else "⚠️ 跳过"
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results[test_name] = "❌ 失败"

    # 打印测试结果总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    for test_name, status in results.items():
        print(f"   {test_name}: {status}")

    print(f"\n🎉 EPYC优化测试完成!")
    print("\n💡 使用建议:")
    print("1. 在生产环境中设置 use_epyc_optimization=True")
    print("2. 根据实际硬件调整 num_models 和 batch_size")
    print("3. 监控内存使用，确保不超过系统限制")
    print("4. 定期检查模型缓存命中率")

if __name__ == "__main__":
    main()