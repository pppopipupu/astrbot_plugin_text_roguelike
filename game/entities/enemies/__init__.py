import pkgutil
import importlib

from . import boss, town_enemies

def _import_all_submodules(package_name):
    package = importlib.import_module(package_name)
    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
        importlib.import_module(module_name)

_import_all_submodules(__name__)

from .base import ALL_ENEMIES, get_enemy_template
