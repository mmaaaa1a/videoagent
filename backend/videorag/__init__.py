# Import VideoRAG from the algorithm implementation to avoid conflicts
import sys
import os

# Add project root directory to path to access VideoRAG-algorithm
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up three levels: __init__.py -> videorag -> backend -> root
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use importlib to import the VideoRAG module directly
import importlib.util
try:
    videorag_init_path = os.path.join(project_root, 'VideoRAG-algorithm', 'videorag', '__init__.py')
    spec = importlib.util.spec_from_file_location("videorag_algorithm_module", videorag_init_path)
    videorag_module = importlib.util.module_from_spec(spec)
    sys.modules["videorag_algorithm_module"] = videorag_module
    spec.loader.exec_module(videorag_module)
    VideoRAG = videorag_module.VideoRAG
    QueryParam = videorag_module.QueryParam
except Exception as e:
    # Fallback: try importing directly
    try:
        import VideoRAG_algorithm.videorag
        VideoRAG = VideoRAG_algorithm.videorag.VideoRAG
        QueryParam = VideoRAG_algorithm.videorag.QueryParam
    except Exception as e2:
        raise ImportError(f"Failed to import VideoRAG from algorithm implementation: {e}, fallback failed: {e2}")