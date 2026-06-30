import os
import json
from typing import Dict, Any

class LocaleManager:
    _data: Dict[str, Any] = {}
    _current_lang: str = "zh_cn"
    _loaded: bool = False

    @classmethod
    def load_locale(cls, lang: str = "zh_cn") -> None:
        cls._current_lang = lang
        cls._data = {}
        
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        locale_dir = os.path.join(current_dir, "data", "locale", lang)
        
        if not os.path.exists(locale_dir):
            return
            
        global_path = os.path.join(locale_dir, "global.json")
        if os.path.exists(global_path):
            try:
                with open(global_path, "r", encoding="utf-8") as f:
                    cls._data.update(json.load(f))
            except Exception:
                pass
                
        npcs_path = os.path.join(locale_dir, "npcs.json")
        if os.path.exists(npcs_path):
            try:
                with open(npcs_path, "r", encoding="utf-8") as f:
                    npcs = json.load(f)
                cls._data["interactive_entities"] = npcs
            except Exception:
                pass
                
        explore_path = os.path.join(locale_dir, "explore.json")
        if os.path.exists(explore_path):
            try:
                with open(explore_path, "r", encoding="utf-8") as f:
                    cls._data.update(json.load(f))
            except Exception:
                pass
                
        cls._loaded = True

    @classmethod
    def get_text(cls, key: str, default: str = "", **kwargs: Any) -> str:
        if not cls._loaded:
            cls.load_locale(cls._current_lang)
            
        keys = key.split(".")
        current = cls._data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                current = None
                break
                
        if current is None:
            return default if default else key
            
        if isinstance(current, str):
            try:
                return current.format(**kwargs)
            except Exception:
                return current
        return str(current)

    @classmethod
    def get_all_translations(cls) -> Dict[str, Any]:
        if not cls._loaded:
            cls.load_locale(cls._current_lang)
        return cls._data
