import os
import pkgutil
import importlib

__all__ = []

def onerror(name):
    raise

def import_all_submodules(package_path, package_name):
    for _, module_name, is_pkg in pkgutil.walk_packages([package_path], prefix=package_name + '.', onerror=onerror):
        importlib.import_module(module_name)
        __all__.append(module_name.split('.')[-1])

import_all_submodules(os.path.dirname(__file__), __package__)
