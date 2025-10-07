#!/usr/bin/env python3
import sys
import os
import torchvision

# Apply global torchvision compatibility fix
if not hasattr(torchvision.transforms, "functional_tensor"):
    import torchvision.transforms.functional as F
    torchvision.transforms.functional_tensor = F
    print("✅ Applied torchvision compatibility fix")

# Fix ImageBind EncodedVideo.from_path() sample_rate parameter issue
def fix_imagebind_sample_rate():
    """Fix ImageBind sample_rate parameter compatibility issue."""
    try:
        import site
        import glob

        # Find ImageBind data.py file
        site_packages = site.getsitepackages()
        data_path = None

        for path in site_packages:
            ib_paths = glob.glob(os.path.join(path, '**', 'imagebind', 'data.py'), recursive=True)
            if ib_paths:
                data_path = ib_paths[0]
                break

        if not data_path:
            print("⚠️  ImageBind data.py not found, skipping sample_rate fix")
            return True

        # Read the file content
        with open(data_path, 'r') as f:
            content = f.read()

        # Check if the problematic code exists
        if 'EncodedVideo.from_path(' in content and '"sample_rate": sample_rate' in content:
            print("🔧 Fixing ImageBind EncodedVideo.from_path() sample_rate parameter...")

            # Fix the problematic call
            fixed_content = content.replace(
                '''video = EncodedVideo.from_path(
            video_path,
            decoder="decord",
            decode_audio=False,
            **{"sample_rate": sample_rate},
        )''',
                '''video = EncodedVideo.from_path(
            video_path,
            decoder="decord",
            decode_audio=False,
        )'''
            )

            # Write back the fixed content
            with open(data_path, 'w') as f:
                f.write(fixed_content)

            print("✅ Fixed ImageBind sample_rate parameter issue")
            return True
        else:
            print("ℹ️  ImageBind sample_rate issue not found or already fixed")
            return True

    except Exception as e:
        print(f"❌ Error fixing ImageBind sample_rate issue: {e}")
        return False

# Apply ImageBind fix
fix_imagebind_sample_rate()

# Test imports after fix
try:
    import pytorchvideo.transforms.augmentations
    print("✅ PyTorchVideo import successful")
except ImportError as e:
    print(f"❌ PyTorchVideo import failed: {e}")

try:
    import imagebind.data
    print("✅ ImageBind import successful")
except ImportError as e:
    print(f"❌ ImageBind import failed: {e}")

# Test CTranslate2
try:
    import ctranslate2
    print("✅ CTranslate2 import successful")
except ImportError as e:
    print(f"❌ CTranslate2 import failed: {e}")

# Test VideoRAG
try:
    import videorag
    print("✅ VideoRAG import successful")
except ImportError as e:
    print(f"❌ VideoRAG import failed: {e}")
