"""
EPYC 64核心处理器配置文件
在项目启动时配置，视频处理时直接使用预配置参数
"""

import os
from typing import Dict, Any

# 全局预配置 - 项目启动时设置一次
_epyc_preconfigured = False
_epyc_config = {}

class EPYCConfig:
    """EPYC处理器配置管理器 - 纯预配置模式，不进行任何检测"""

    def __init__(self):
        # 纯预配置模式，不进行任何系统检测
        pass

    def get_optimal_config(self) -> Dict[str, Any]:
        """直接使用预配置，不进行任何计算"""
        global _epyc_preconfigured, _epyc_config

        # 确保已初始化
        if not _epyc_preconfigured:
            initialize_epyc_once()

        return _epyc_config.copy()

    def apply_environment_variables(self, config: Dict[str, Any]) -> None:
        """不再应用环境变量，已在初始化时设置"""
        pass

    def print_system_info(self) -> None:
        """不再打印系统信息，已在初始化时打印"""
        pass

    def print_config(self, config: Dict[str, Any]) -> None:
        """不再打印配置信息，已在初始化时打印"""
        pass

def get_epyc_config() -> EPYCConfig:
    """获取EPYC配置实例"""
    return EPYCConfig()

def initialize_epyc_once() -> None:
    """项目启动时一次性初始化EPYC配置"""
    global _epyc_preconfigured, _epyc_config

    if _epyc_preconfigured:
        return  # 已经配置过了

    print("🚀 初始化EPYC优化配置 (项目启动时执行一次)")

    # 从环境变量读取预配置
    _epyc_config = {
        'use_epyc_optimization': os.getenv('USE_EPYC_OPTIMIZATION', 'false').lower() == 'true',
        'num_models': int(os.getenv('EPYC_NUM_MODELS', '8')),
        'batch_size': int(os.getenv('EPYC_BATCH_SIZE', '32')),
        'workers': int(os.getenv('EPYC_WORKERS', '64')),
        'compute_type': os.getenv('EPYC_COMPUTE_TYPE', 'float32'),
        'system_type': 'epyc',
        'optimization_level': 'preconfigured'
    }

    # 一次性设置环境变量
    if _epyc_config['use_epyc_optimization']:
        env_vars = {
            'OMP_NUM_THREADS': os.getenv('OMP_NUM_THREADS', '8'),
            'MKL_NUM_THREADS': os.getenv('MKL_NUM_THREADS', '8'),
            'OPENBLAS_NUM_THREADS': os.getenv('OPENBLAS_NUM_THREADS', '8'),
            'NUMEXPR_NUM_THREADS': os.getenv('NUMEXPR_NUM_THREADS', '8'),
            'MALLOC_ARENA_MAX': os.getenv('MALLOC_ARENA_MAX', '8')
        }

        for var, value in env_vars.items():
            os.environ[var] = value
            print(f"✅ 设置环境变量: {var}={value}")

        print(f"✅ EPYC配置已预加载: 模型数={_epyc_config['num_models']}, 批量大小={_epyc_config['batch_size']}, 工作进程数={_epyc_config['workers']}")

    _epyc_preconfigured = True
    print("🎯 EPYC配置初始化完成，后续视频处理将直接使用预配置")

def get_epyc_config() -> EPYCConfig:
    """获取EPYC配置实例"""
    return EPYCConfig()

def setup_epyc_environment() -> Dict[str, Any]:
    """获取预配置的EPYC环境 (视频处理时调用，不重新初始化)"""
    global _epyc_preconfigured, _epyc_config

    # 如果还没有初始化，先初始化
    if not _epyc_preconfigured:
        initialize_epyc_once()

    # 直接返回预配置，不进行任何检测和设置
    return _epyc_config.copy()

if __name__ == "__main__":
    # 测试配置
    config = setup_epyc_environment()
    print(f"\n🚀 EPYC环境配置完成: {config['system_type']}")