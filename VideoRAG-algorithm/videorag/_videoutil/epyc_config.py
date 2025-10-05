"""
EPYC 64核心处理器配置文件
用于自动检测和配置EPYC处理器的最佳性能参数
"""

import os
import subprocess
import platform
from typing import Dict, Any

class EPYCConfig:
    """EPYC处理器配置管理器"""

    def __init__(self):
        self.system_info = self._detect_system_info()
        self.is_epyc = self._is_epyc_processor()
        self.core_count = self._get_core_count()

    def _detect_system_info(self) -> Dict[str, Any]:
        """检测系统信息"""
        info = {
            'platform': platform.system(),
            'processor': platform.processor(),
            'machine': platform.machine()
        }

        try:
            # Linux系统获取CPU信息
            if info['platform'] == 'Linux':
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()

                # 提取关键信息
                lines = cpuinfo.split('\n')
                for line in lines:
                    if 'model name' in line:
                        info['cpu_model'] = line.split(':')[1].strip()
                    elif 'cpu cores' in line:
                        info['physical_cores'] = int(line.split(':')[1].strip())
                    elif 'siblings' in line:
                        info['logical_cores'] = int(line.split(':')[1].strip())

                # 检查是否是EPYC处理器
                if 'epyc' in info.get('cpu_model', '').lower():
                    info['is_epyc'] = True
                else:
                    info['is_epyc'] = False

        except Exception as e:
            print(f"⚠️ 系统信息检测失败: {e}")

        return info

    def _is_epyc_processor(self) -> bool:
        """检查是否为EPYC处理器"""
        return self.system_info.get('is_epyc', False)

    def _get_core_count(self) -> int:
        """获取CPU核心数"""
        return self.system_info.get('physical_cores', os.cpu_count() or 8)

    def get_optimal_config(self) -> Dict[str, Any]:
        """获取EPYC优化配置"""
        if not self.is_epyc:
            print("⚠️ 检测到非EPYC处理器，使用通用配置")
            return self._get_generic_config()

        # EPYC专用配置
        config = {
            'system_type': 'epyc',
            'core_count': self.core_count,
            'optimization_level': 'aggressive',

            # CPU并行配置
            'omp_num_threads': min(16, self.core_count // 4),  # 使用1/4核心做OMP
            'mkl_num_threads': min(16, self.core_count // 4),
            'openblas_num_threads': min(16, self.core_count // 4),
            'numexpr_num_threads': min(16, self.core_count // 4),

            # 模型配置
            'num_models': min(8, self.core_count // 8),  # 每8核心一个模型实例
            'batch_size': min(32, self.core_count // 2),  # 批量大小
            'workers': min(64, self.core_count),  # 工作进程数

            # 内存配置
            'compute_type': 'float32',  # EPYC通常有充足内存
            'model_cache_size': 5,  # 模型缓存数量

            # 系统优化
            'cpu_governor': 'performance',
            'enable_hugepages': True,
            'cpu_affinity': True
        }

        # 根据核心数调整配置
        if self.core_count >= 64:
            # 64核心或以上的EPYC
            config.update({
                'omp_num_threads': 16,
                'num_models': 8,
                'batch_size': 32,
                'workers': 64
            })
        elif self.core_count >= 32:
            # 32核心EPYC
            config.update({
                'omp_num_threads': 8,
                'num_models': 4,
                'batch_size': 16,
                'workers': 32
            })
        else:
            # 少核心EPYC
            config.update({
                'omp_num_threads': 4,
                'num_models': 2,
                'batch_size': 8,
                'workers': self.core_count
            })

        return config

    def _get_generic_config(self) -> Dict[str, Any]:
        """通用处理器配置"""
        config = {
            'system_type': 'generic',
            'core_count': self.core_count,
            'optimization_level': 'moderate',

            # 保守的并行配置
            'omp_num_threads': min(4, self.core_count),
            'mkl_num_threads': min(4, self.core_count),
            'openblas_num_threads': min(4, self.core_count),
            'numexpr_num_threads': min(4, self.core_count),

            # 模型配置
            'num_models': min(2, max(1, self.core_count // 8)),
            'batch_size': min(8, self.core_count),
            'workers': min(8, self.core_count),

            # 内存配置
            'compute_type': 'int8',  # 通用配置使用int8节省内存
            'model_cache_size': 2,

            # 系统优化
            'cpu_governor': 'ondemand',
            'enable_hugepages': False,
            'cpu_affinity': False
        }

        return config

    def apply_environment_variables(self, config: Dict[str, Any]) -> None:
        """应用环境变量配置"""
        env_vars = {
            'OMP_NUM_THREADS': config.get('omp_num_threads', 4),
            'MKL_NUM_THREADS': config.get('mkl_num_threads', 4),
            'OPENBLAS_NUM_THREADS': config.get('openblas_num_threads', 4),
            'NUMEXPR_NUM_THREADS': config.get('numexpr_num_threads', 4),
            'MALLOC_ARENA_MAX': '4'
        }

        for key, value in env_vars.items():
            os.environ[key] = str(value)
            print(f"✅ 设置环境变量: {key}={value}")

    def apply_system_optimizations(self, config: Dict[str, Any]) -> None:
        """应用系统级优化"""
        if config.get('system_type') != 'epyc':
            print("⚠️ 非EPYC系统，跳过系统级优化")
            return

        # CPU调度器优化
        if config.get('cpu_governor') == 'performance':
            try:
                subprocess.run(['sudo', 'cpupower', 'frequency-set', '-g', 'performance'],
                              capture_output=True, check=False, timeout=5)
                print("✅ CPU调度器设置为性能模式")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                print("⚠️ 无法设置CPU调度器 (需要root权限)")

        # 大页面支持
        if config.get('enable_hugepages'):
            try:
                with open('/proc/sys/vm/nr_hugepages', 'w') as f:
                    f.write('1024')
                print("✅ 大页面支持已启用")
            except (PermissionError, FileNotFoundError):
                print("⚠️ 无法启用大页面 (需要root权限)")

    def print_system_info(self) -> None:
        """打印系统信息"""
        print("🖥️  系统信息:")
        print(f"   - 操作系统: {self.system_info.get('platform', 'Unknown')}")
        print(f"   - 处理器: {self.system_info.get('cpu_model', 'Unknown')}")
        print(f"   - 物理核心: {self.system_info.get('physical_cores', 'Unknown')}")
        print(f"   - 逻辑核心: {self.system_info.get('logical_cores', 'Unknown')}")
        print(f"   - EPYC处理器: {'是' if self.is_epyc else '否'}")

    def print_config(self, config: Dict[str, Any]) -> None:
        """打印配置信息"""
        print(f"\n⚙️  {config.get('system_type', 'Unknown').upper()} 优化配置:")
        print(f"   - 优化级别: {config.get('optimization_level', 'Unknown')}")
        print(f"   - OMP线程数: {config.get('omp_num_threads', 'Unknown')}")
        print(f"   - 模型实例数: {config.get('num_models', 'Unknown')}")
        print(f"   - 批量大小: {config.get('batch_size', 'Unknown')}")
        print(f"   - 工作进程数: {config.get('workers', 'Unknown')}")
        print(f"   - 计算类型: {config.get('compute_type', 'Unknown')}")

def get_epyc_config() -> EPYCConfig:
    """获取EPYC配置实例"""
    return EPYCConfig()

def setup_epyc_environment() -> Dict[str, Any]:
    """设置EPYC环境并返回配置"""
    epyc_config = get_epyc_config()

    # 打印系统信息
    epyc_config.print_system_info()

    # 获取优化配置
    config = epyc_config.get_optimal_config()

    # 打印配置信息
    epyc_config.print_config(config)

    # 应用环境变量
    epyc_config.apply_environment_variables(config)

    # 应用系统优化
    epyc_config.apply_system_optimizations(config)

    return config

if __name__ == "__main__":
    # 测试配置
    config = setup_epyc_environment()
    print(f"\n🚀 EPYC环境配置完成: {config['system_type']}")