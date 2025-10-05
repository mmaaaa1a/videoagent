#!/usr/bin/env python3
"""
PyTorchVideo Torchvision Compatibility Fix Script

This script fixes the compatibility issue between PyTorchVideo and the current
torchvision version by patching import statements in PyTorchVideo's source code.
"""

import sys
import os
import traceback
import glob
import site

def find_pytorchvideo_path():
    """Find PyTorchVideo installation path manually since import might fail."""
    try:
        # Try to find pytorchvideo in site-packages
        site_packages = site.getsitepackages()
        for path in site_packages:
            video_paths = glob.glob(os.path.join(path, '**', 'pytorchvideo', 'transforms', 'augmentations.py'),
                                   recursive=True)
            if video_paths:
                return video_paths[0]
        return None
    except Exception:
        return None

def fix_pytorchvideo_compatibility():
    """Fix PyTorchVideo torchvision compatibility issue."""
    print("🔧 Starting PyTorchVideo compatibility fix...")

    # First, try to import normally
    aug_path = None
    try:
        import pytorchvideo.transforms.augmentations as pv_aug
        print("✅ PyTorchVideo successfully imported")
        aug_file = pv_aug.__file__
        aug_dir = os.path.dirname(aug_file)
        aug_path = os.path.join(aug_dir, 'augmentations.py')
    except ImportError:
        print("⚠️  PyTorchVideo cannot be imported directly, trying to find files manually...")
        aug_path = find_pytorchvideo_path()
        if not aug_path:
            print("❌ Cannot locate PyTorchVideo augmentations.py file")
            return False
        print(f"📁 Found PyTorchVideo augmentations at: {aug_path}")

    # Check if file exists and read content
    if not os.path.exists(aug_path):
        print(f"❌ PyTorchVideo augmentations file not found at: {aug_path}")
        return False

    try:
        # Read the file content
        with open(aug_path, 'r') as f:
            content = f.read()

        # Check if the problematic import exists
        if 'torchvision.transforms.functional_tensor' in content:
            print("🔍 Found problematic import in PyTorchVideo, fixing...")

            # Create fixed content
            fixed_content = content.replace(
                'import torchvision.transforms.functional_tensor as F_t',
                'import torchvision.transforms.functional as F'
            )
            fixed_content = fixed_content.replace('F_t.', 'F.')

            # Write back the fixed content
            with open(aug_path, 'w') as f:
                f.write(fixed_content)

            print("✅ PyTorchVideo torchvision compatibility fixed successfully")
            return True
        else:
            print("ℹ️  No problematic import found in PyTorchVideo")
            return True

    except Exception as e:
        print(f"❌ Error during PyTorchVideo fix: {e}")
        traceback.print_exc()
        return False

def verify_pytorchvideo_import():
    """Verify that PyTorchVideo can be imported after fixes."""
    print("🔍 Verifying PyTorchVideo import...")

    try:
        import pytorchvideo.transforms.augmentations
        print("✅ PyTorchVideo import verification successful")
        return True
    except ImportError as e:
        print(f"❌ PyTorchVideo import still fails: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during PyTorchVideo verification: {e}")
        return False

def main():
    """Main entry point."""
    print("🚀 PyTorchVideo Compatibility Fix Script")
    print("=" * 50)

    # Fix compatibility issue
    if fix_pytorchvideo_compatibility():
        print("✅ Fix process completed")
    else:
        print("❌ Fix process failed")
        sys.exit(1)

    # Verify the fix worked
    print()
    if verify_pytorchvideo_import():
        print("🎉 PyTorchVideo compatibility fix completed successfully!")
    else:
        print("❌ PyTorchVideo compatibility fix verification failed")
        sys.exit(1)

if __name__ == "__main__":
    main()