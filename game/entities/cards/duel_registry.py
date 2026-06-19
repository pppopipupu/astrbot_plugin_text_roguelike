DUEL_CARD_CLASS_REGISTRY = {}

def register_duel_card(cid, **kwargs):
    def decorator(cls):
        DUEL_CARD_CLASS_REGISTRY[cid] = (cls, kwargs)
        return cls
    return decorator
