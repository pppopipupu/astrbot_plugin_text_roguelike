from typing import Any
from ..core.locale_manager import LocaleManager

def get_locale_text(key: str, **kwargs: Any) -> str:
    return LocaleManager.get_text(key, **kwargs)
