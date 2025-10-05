#!/usr/bin/env python3
"""
ImageBind Torchvision Compatibility Fix Script

This script fixes the compatibility issue between ImageBind and the current
torchvision version by patching import statements in ImageBind's source code.
"""

import sys
import os
import traceback
import site

def find_imagebind_path():
    """Find ImageBind installation path manually since import might fail."""
    try:
        # Try to find imagebind in site-packages
        site_packages = site.getsitepackages()
        for path in site_packages:
            # Look for imagebind directory or __init__.py
            import glob
            ib_paths = glob.glob(os.path.join(path, '**', 'imagebind', '__init__.py'), recursive=True)
            if ib_paths:
                return os.path.dirname(ib_paths[0])
        return None
    except Exception:
        return None

def fix_imagebind_compatibility():
    """Fix ImageBind torchvision compatibility issue."""
    print("🔧 Starting ImageBind compatibility fix...")

    # Find ImageBind data.py file
    ib_path = None
    try:
        import imagebind
        ib_path = os.path.dirname(imagebind.__file__)
        print("✅ ImageBind imported successfully")
    except ImportError:
        print("⚠️  ImageBind cannot be imported directly, trying to find files manually...")
        ib_path = find_imagebind_path()
        if not ib_path:
            print("❌ Cannot locate ImageBind directory")
            return False
        print(f"📁 Found ImageBind at: {ib_path}")

    # Look for data.py file
    data_path = os.path.join(ib_path, 'data.py')
    if not os.path.exists(data_path):
        print(f"❌ ImageBind data.py not found at: {data_path}")
        return False
    print(f"📁 Found ImageBind data.py at: {data_path}")

    try:
        # Read the file content
        with open(data_path, 'r') as f:
            content = f.read()

        # Check if the problematic import exists
        if 'torchvision.transforms.functional_tensor' in content:
            print("🔍 Found problematic import in ImageBind, fixing...")

            # Create fixed content - same fix as the original inline script
            fixed_content = content.replace(
                'import torchvision.transforms.functional_tensor as F_t',
                'from torchvision.transforms import functional as F'
            )
            fixed_content = fixed_content.replace('F_t.', 'F.')

            # Write back the fixed content
            with open(data_path, 'w') as f:
                f.write(fixed_content)

            print("✅ ImageBind torchvision compatibility fixed successfully")
            return True
        else:
            print("ℹ️  No problematic import found in ImageBind")
            return True

    except Exception as e:
        print(f"❌ Error during ImageBind fix: {e}")
        traceback.print_exc()
        return False

def verify_imagebind_import():
    """Verify that ImageBind can be imported after fixes."""
    print("🔍 Verifying ImageBind import...")

    try:
        import imagebind.data
        print("✅ ImageBind import verification successful")
        return True
    except ImportError as e:
        print(f"❌ ImageBind import still fails: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during ImageBind verification: {e}")
        return False

def main():
    """Main entry point."""
    print("🚀 ImageBind Compatibility Fix Script")
    print("=" * 50)

    # Fix compatibility issue
    if fix_imagebind_compatibility():
        print("✅ Fix process completed")
    else:
        print("❌ Fix process failed")
        sys.exit(1)

    # Verify the fix worked
    print()
    if verify_imagebind_import():
        print("🎉 ImageBind compatibility fix completed successfully!")
    else:
        print("❌ ImageBind compatibility fix verification failed")
        sys.exit(1)

if __name__ == "__main__":
    main()