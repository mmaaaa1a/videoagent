#!/usr/bin/env python3
import sys
import torchvision
# Apply global torchvision compatibility fix
if not hasattr(torchvision.transforms, "functional_tensor"):
    import torchvision.transforms.functional as F
    torchvision.transforms.functional_tensor = F
    print("✅ Applied torchvision compatibility fix")

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
