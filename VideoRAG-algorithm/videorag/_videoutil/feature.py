import os
import torch
import pickle
from tqdm import tqdm

# Fix for torchvision compatibility before importing imagebind
import torchvision
import torchvision.transforms.functional as F
import sys
# Monkey patch the missing module
if not hasattr(torchvision.transforms, 'functional_tensor'):
    torchvision.transforms.functional_tensor = F

# Now import imagebind after the fix
from imagebind import data
from imagebind.models import imagebind_model
from imagebind.models.imagebind_model import ImageBindModel, ModalityType


def encode_video_segments(video_paths, embedder: ImageBindModel):
    device = next(embedder.parameters()).device
    inputs = {
        ModalityType.VISION: data.load_and_transform_video_data(video_paths, device),
    }
    with torch.no_grad():
        embeddings = embedder(inputs)[ModalityType.VISION]
    embeddings = embeddings.cpu()
    return embeddings

def encode_string_query(query:str, embedder: ImageBindModel):
    device = next(embedder.parameters()).device
    inputs = {
        ModalityType.TEXT: data.load_and_transform_text([query], device),
    }
    with torch.no_grad():
        embeddings = embedder(inputs)[ModalityType.TEXT]
    embeddings = embeddings.cpu()
    return embeddings