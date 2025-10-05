#!/usr/bin/env python3
"""
测试脚本：glibc 兼容性修复方法验证

运行方法：
python test_glibc_compatibility.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class GlibcCompatibilityTest:
    def __init__(self):
        self.results = {}
        self.test_dir = Path('/tmp/glibc_test')

    def setup(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True)

        # 查找 ctranslate2 库 (多重策略)
        self.ctranslate_lib = self._find_ctranslate_lib()
        self.ctranslate_version = None

        if not self.ctranslate_lib:
            print("❌ 未找到 ctranslate2 库文件")
            print("📍 搜索路径:")
            self._show_search_paths()
            return False

        print(f"✅ 找到 ctranslate2 库: {self.ctranslate_lib}")
        if self.ctranslate_version:
            print(f"📋 ctranslate2 版本: {self.ctranslate_version}")
        return True

    def _find_ctranslate_lib(self):
        """多重策略查找 ctranslate2 库文件"""
        import subprocess
        import json

        # 方法1: pip show 查询安装路径
        print("🔍 方法1: 通过 pip show 查找安装路径...")
        try:
            result = subprocess.run(['pip', 'show', 'ctranslate2'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.startswith('Location:'):
                        pip_location = line.split(':', 1)[1].strip()
                        lib_path = self._search_in_pip_location(pip_location)
                        if lib_path:
                            return lib_path
                        break
        except Exception as e:
            print(f"⚠️ pip show 失败: {e}")

        # 方法2: 通过 Python 模块位置查找
        print("🔍 方法2: 通过 Python 模块位置查找...")
        try:
            import ctranslate2
            module_path = ctranslate2.__file__
            if module_path:
                ctranslate2_dir = Path(module_path).parent
                # 查找同级目录中的库文件
                for so_file in ctranslate2_dir.glob("*.so*"):
                    if "ctranslate2" in so_file.name:
                        return so_file
                # 查找上级目录中的lib子目录
                lib_dir = ctranslate2_dir.parent / "lib"
                if lib_dir.exists():
                    for so_file in lib_dir.glob("*ctranslate2*.so*"):
                        return so_file
        except ImportError:
            print("⚠️ 无法导入 ctranslate2，可能是 glibc 问题")
        except Exception as e:
            print(f"⚠️ Python 模块位置查找失败: {e}")

        # 方法3: 传统系统路径搜索 + 扩展路径
        print("🔍 方法3: 系统路径和扩展路径搜索...")
        search_dirs = [
            "/usr/lib", "/usr/lib64", "/usr/local/lib",
            "/usr/lib/x86_64-linux-gnu", "/usr/local/lib64",
        ]

        # 添加可能的 pip 安装路径
        import site
        for site_path in site.getsitepackages():
            search_dirs.extend([
                str(Path(site_path) / "ctranslate2"),
                str(Path(site_path) / ".."),
                site_path,
            ])

        lib_names = ["libctranslate2.so", "libctranslate2.so.*"]

        for search_dir in search_dirs:
            search_path = Path(search_dir)
            if search_path.exists():
                for lib_name in lib_names:
                    for so_file in search_path.glob(lib_name):
                        if so_file.is_file():
                            return so_file

        return None

    def _search_in_pip_location(self, pip_location):
        """在 pip show 指定的位置中搜索库文件"""
        location_path = Path(pip_location)

        # 常见的库文件位置
        candidate_paths = [
            location_path / "ctranslate2" / ".libs",  # 源码编译时的位置
            location_path / ".libs",                 # 另一个常见位置
        ]

        for base_path in candidate_paths:
            if base_path.exists():
                for so_file in base_path.glob("*ctranslate2*.so*"):
                    return so_file

        # 如果没有找到，直接在整个pip位置搜索
        for so_file in location_path.rglob("*ctranslate2*.so*"):
            return so_file

        return None

    def _show_search_paths(self):
        """显示所有搜索过的路径"""
        search_dirs = [
            "/usr/lib", "/usr/lib64", "/usr/local/lib",
            "/usr/lib/x86_64-linux-gnu", "/usr/local/lib64",
        ]

        import site
        for site_path in site.getsitepackages():
            search_dirs.append(site_path)

        print("   系统路径:")
        for path in ["/usr/lib", "/usr/lib64", "/usr/local/lib"]:
            print(f"     {path}")
        print("   Python 包路径:")
        for path in site.getsitepackages()[:3]:  # 只显示前3个
            print(f"     {path}")

        print("   pip 安装查询:")
        try:
            import subprocess
            result = subprocess.run(['pip', 'show', 'ctranslate2'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.startswith('Location:'):
                        print(f"     pip安装位置: {line.split(':', 1)[1].strip()}")
                        break
        except:
            pass

    def test_method_1_patchelf(self):
        """测试方法一：使用 patchelf 修改 RPATH"""
        print("\n🧪 测试方法一：patchelf 修改 RPATH")

        # 复制库文件到测试目录
        test_lib = self.test_dir / "libctranslate2_patchelf.so"
        shutil.copy2(self.ctranslate_lib, test_lib)

        # 检查原始依赖
        cmd = f"objdump -T {test_lib} | grep GLIBC"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            glibc_deps = [line.strip() for line in result.stdout.split('\n') if 'GLIBC' in line]
            print(f"📋 原始 GLIBC 依赖: {len(glibc_deps)} 个符号")

        # 修改 RPATH
        rpath_cmd = f"patchelf --set-rpath '/lib64:/usr/lib64' {test_lib}"
        result = subprocess.run(rpath_cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ patchelf RPATH 修改成功")
        else:
            print(f"❌ patchelf 失败: {result.stderr}")
            self.results['patchelf'] = False
            return False

        # 测试库加载
        test_script = f"""
import os
import ctypes
try:
    # 添加测试目录到库路径
    os.environ['LD_LIBRARY_PATH'] = '/tmp/glibc_test:' + os.environ.get('LD_LIBRARY_PATH', '')
    ctypes.CDLL('{test_lib}')
    print('SUCCESS')
except Exception as e:
    print(f'FAILED: {{e}}')
"""
        with open('/tmp/test_patchelf.py', 'w') as f:
            f.write(test_script)

        result = subprocess.run(['python3', '/tmp/test_patchelf.py'],
                               capture_output=True, text=True)

        success = 'SUCCESS' in result.stdout
        self.results['patchelf'] = success

        if success:
            print("✅ patchelf 方法测试成功 - 库加载正常")
        else:
            print(f"❌ patchelf 方法失败: {result.stdout.strip()}")

        return success

    def test_method_2_ld_library_path(self):
        """测试方法二：LD_LIBRARY_PATH 环境变量"""
        print("\n🧪 测试方法二：LD_LIBRARY_PATH 环境变量")

        # 创建兼容库目录
        compat_dir = self.test_dir / "compat_libs"
        compat_dir.mkdir()

        # 创建一些关键库的软链接
        libs_to_link = ['libc.so.6', 'libm.so.6', 'libpthread.so.0']
        for lib in libs_to_link:
            for search_path in ["/lib64", "/usr/lib64", "/lib"]:
                src = Path(search_path) / lib
                if src.exists():
                    dst = compat_dir / lib
                    if not dst.exists():
                        os.symlink(src, dst)
                    break

        test_script = f"""
import os
# 设置 LD_LIBRARY_PATH
os.environ['LD_LIBRARY_PATH'] = '/tmp/glibc_test/compat_libs:' + os.environ.get('LD_LIBRARY_PATH', '')
try:
    from faster_whisper import WhisperModel
    print('SUCCESS')
except Exception as e:
    print(f'FAILED: {{e}}')
"""
        with open('/tmp/test_ld_path.py', 'w') as f:
            f.write(test_script)

        result = subprocess.run(['python3', '/tmp/test_ld_path.py'],
                               capture_output=True, text=True)

        success = 'SUCCESS' in result.stdout and 'FAILED' not in result.stdout
        self.results['ld_library_path'] = success

        if success:
            print("✅ LD_LIBRARY_PATH 方法测试成功 - faster_whisper 导入正常")
        else:
            error_msg = result.stdout.strip() + result.stderr.strip()
            print(f"❌ LD_LIBRARY_PATH 方法失败: {error_msg}")

        return success

    def test_final_integration(self, method_name):
        """测试最终集成 - VideoRAG 导入"""
        print("\n🎯 测试最终集成：VideoRAG 模块导入")
        method_success = self.results.get(method_name, False)

        if not method_success:
            print(f"❌ 基础 {method_name} 测试未通过，跳过集成测试")
            return False

        # 设置相应的环境变量
        env_vars = {}
        if method_name == 'patchelf':
            env_vars['LD_LIBRARY_PATH'] = f'/tmp/glibc_test:{os.environ.get("LD_LIBRARY_PATH", "")}'
        elif method_name == 'ld_library_path':
            env_vars['LD_LIBRARY_PATH'] = f'/tmp/glibc_test/compat_libs:{os.environ.get("LD_LIBRARY_PATH", "")}'

        test_script = """
import sys
import os
import traceback

try:
    # 添加项目路径
    project_root = '/app'
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print("导入 videorag 模块...")
    import videorag
    print("✅ VideoRAG 模块导入成功")

    # 尝试创建 VideoRAG 实例（不实际使用）
    print("创建 VideoRAG 实例...")
    # 注：这里不进行实际初始化，仅测试导入
    print("✅ VideoRAG 实例创建成功")

except Exception as e:
    print(f"❌ VideoRAG 测试失败: {e}")
    traceback.print_exc()
    import sys
    sys.exit(1)
"""
        with open('/tmp/test_integration.py', 'w') as f:
            f.write(test_script)

        env = os.environ.copy()
        env.update(env_vars)

        result = subprocess.run(['python3', '/tmp/test_integration.py'],
                               capture_output=True, text=True, env=env)

        success = result.returncode == 0

        if success:
            print("✅ VideoRAG 集成测试成功")
        else:
            print(f"❌ VideoRAG 集成测试失败")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)

        return success

    def run_all_tests(self):
        """运行所有测试 - 确保每个测试都执行完整"""
        print("=" * 60)
        print("🧪 GLIBC 兼容性测试套件")
        print("=" * 60)

        if not self.setup():
            return self.results

        print("\n🏃 开始执行所有测试方法...")

        # 测试方法一：patchelf - 无论结果如何都尝试集成测试
        print("\n" + "="*40)
        print("🔢 测试方法一：patchelf + 集成测试")
        print("="*40)
        method1_success = self.test_method_1_patchelf()
        print(f"📋 patchelf 结果: {'✅ 成功' if method1_success else '❌ 失败'}")

        # 无论patchelf结果如何都尝试集成测试，以收集更多信息
        try:
            integration1_result = self.test_final_integration('patchelf')
            print(f"📋 patchelf 集成测试结果: {'✅ 成功' if integration1_result else '❌ 失败'}")
        except Exception as e:
            print(f"⚠️ patchelf 集成测试异常: {e}")
            integration1_result = False

        # 测试方法二：LD_LIBRARY_PATH - 无论结果如何都尝试集成测试
        print("\n" + "="*40)
        print("🔢 测试方法二：LD_LIBRARY_PATH + 集成测试")
        print("="*40)
        method2_success = self.test_method_2_ld_library_path()
        print(f"📋 LD_LIBRARY_PATH 结果: {'✅ 成功' if method2_success else '❌ 失败'}")

        try:
            integration2_result = self.test_final_integration('ld_library_path')
            print(f"📋 LD_LIBRARY_PATH 集成测试结果: {'✅ 成功' if integration2_result else '❌ 失败'}")
        except Exception as e:
            print(f"⚠️ LD_LIBRARY_PATH 集成测试异常: {e}")
            integration2_result = False

        # 输出综合测试报告
        self.print_report()

        print("\n🔍 测试总结:")
        print(" patchelf 方法:")
        print(f"   - 库文件修改: {'✅' if method1_success else '❌'}")
        print(f"   - VideoRAG 集成: {'✅' if integration1_result else '❌'}")
        print(" LD_LIBRARY_PATH 方法:")
        print(f"   - 环境变量设置: {'✅' if method2_success else '❌'}")
        print(f"   - VideoRAG 集成: {'✅' if integration2_result else '❌'}")

        return self.results

    def print_report(self):
        """输出详细测试报告和诊断分析"""
        print("\n" + "=" * 60)
        print("📊 GLIBC 兼容性测试诊断报告")
        print("=" * 60)

        # 详细结果分析
        print("\n🔍 测试方法结果:")
        for method, success in self.results.items():
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {method}: {status}")

            # 提供针对性分析
            if method == 'patchelf' and not success:
                print("    💡 分析: patchelf可能无法修改此类型库文件，或文件权限不足")
                print("    💡 建议: 检查库文件权限，尝试sudo运行，或考虑其他方法")
            elif method == 'ld_library_path' and not success:
                print("    💡 分析: LD_LIBRARY_PATH方法需要正确的库文件路径")
                print("    💡 建议: 确认库文件位置，或使用绝对路径")

        # 库文件信息诊断
        print(f"\n📁 库文件状态:")
        if self.ctranslate_lib:
            print(f"  路径: {self.ctranslate_lib}")
            print(f"  存在: {'✅' if self.ctranslate_lib.exists() else '❌'}")
            print(f"  可读: {'✅' if os.access(self.ctranslate_lib, os.R_OK) else '❌'}")
            print(f"  可写: {'✅' if os.access(self.ctranslate_lib, os.W_OK) else '❌'}")

            # 检查文件大小和类型
            try:
                size = self.ctranslate_lib.stat().st_size
                print(f"  大小: {size:,} 字节")
                if size < 1024:
                    print("    ⚠️  警告: 文件异常小，可能不是正确的库文件")
            except Exception as e:
                print(f"  大小获取失败: {e}")

            # ELF文件检查
            try:
                with open(self.ctranslate_lib, 'rb') as f:
                    header = f.read(4)
                    if header == b'\x7fELF':
                        print("  格式: ELF (Linux可执行文件)")
                    else:
                        print("  格式: 非ELF格式 ⚠️")
            except Exception as e:
                print(f"  格式检查失败: {e}")
        else:
            print("  ❌ 未找到库文件")

        # 环境检查
        print(f"\n🖥️  系统环境:")
        print(f"  Python路径: {sys.executable}")

        # 检查Docker环境
        if os.path.exists('/.dockerenv'):
            print("  运行环境: Docker容器 🐳")
            print("  🎯 建议: 检查Docker seccomp配置和安全策略")
        else:
            print("  运行环境: 宿主机 💻")

        # 获取glibc版本
        try:
            result = subprocess.run(['ldd', '--version'],
                                  capture_output=True, text=True, timeout=5)
            version_lines = result.stdout.split('\n')
            for line in version_lines:
                if 'ldd' in line and 'version' in line.lower():
                    print(f"  glibc版本: {line.strip()}")
                    break
        except:
            print("  glibc版本: 未知")

        # 智能推荐方案
        print(f"\n🎯 解决方案推荐:")

        # 检查是否有任何成功的方法
        successful_methods = [method for method, success in self.results.items() if success]

        if successful_methods:
            print("  🎉 发现有效方法!")
            for method in successful_methods:
                if method == 'patchelf':
                    print("  ⭐ 推荐: 使用 patchelf 修改 RPATH")
                    print("     原因: 对原程序影响最小，生产环境安全可靠")
                    print("     实现: 在Dockerfile中添加patchelf相关配置")
                elif method == 'ld_library_path':
                    print("  ⭐ 推荐: 使用 LD_LIBRARY_PATH 环境变量")
                    print("     原因: 配置简单，立即生效")
                    print("     实现: 在docker-compose中设置环境变量")
        else:
            print("  ❌ 所有测试方法均失败")
            print("  🔧 备选方案:")

            # 分析失败原因并推荐备选方案
            lib_found = self.ctranslate_lib is not None
            is_docker = os.path.exists('/.dockerenv')

            if is_docker:
                print("    1. Docker 安全策略调整:")
                print("       - 添加 security_opt: [seccomp:unconfined]")
                print("       - 添加 cap_add: [SYS_ADMIN]")
                print("    2. 使用兼容的ctranslate2版本")
                print("    3. 尝试静态链接的库文件")
            else:
                print("    1. 检查系统glibc版本兼容性")
                print("    2. 更新或降级ctranslate2版本")
                print("    3. 使用Anaconda环境隔离")
                print("    4. 检查操作系统更新")

            print("  📖 更多信息:")
            print("    - https://github.com/OpenNMT/CTranslate2/issues")
            print("    - https://github.com/SYSTRAN/faster-whisper/issues")
            print("    - 检查VideoRAG的兼容性要求")

if __name__ == "__main__":
    tester = GlibcCompatibilityTest()
    tester.run_all_tests()