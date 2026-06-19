DUEL_BUFF_CLASS_REGISTRY = {}

def register_duel_buff(buff_id: str):
    def decorator(cls):
        DUEL_BUFF_CLASS_REGISTRY[buff_id] = cls
        return cls
    return decorator
