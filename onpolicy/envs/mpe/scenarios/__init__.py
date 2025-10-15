import importlib.util
import os.path as osp
import sys
from uuid import uuid4
from types import ModuleType

def load(name: str) -> ModuleType:
    """Dynamically load a Python module from a path relative to this file."""
    pathname = osp.join(osp.dirname(__file__), name)
    if not osp.isfile(pathname):
        raise FileNotFoundError(pathname)

    # Give it a unique name to avoid collisions in sys.modules
    module_name = f"_dynamic_{osp.splitext(osp.basename(name))[0]}_{uuid4().hex}"

    spec = importlib.util.spec_from_file_location(module_name, pathname)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create spec for {pathname}")

    module = importlib.util.module_from_spec(spec)
    # Register so imports inside the loaded module (if any) can resolve by name
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
