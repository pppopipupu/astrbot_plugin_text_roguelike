BUFF_CLASS_REGISTRY = {}

def register_buff(buff_id: str):
    def decorator(cls):
        BUFF_CLASS_REGISTRY[buff_id] = cls
        return cls
    return decorator
