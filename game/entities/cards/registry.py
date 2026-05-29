CARD_CLASS_REGISTRY = {}

def register_card(cid, **kwargs):
    def decorator(cls):
        CARD_CLASS_REGISTRY[cid] = (cls, kwargs)
        return cls
    return decorator
