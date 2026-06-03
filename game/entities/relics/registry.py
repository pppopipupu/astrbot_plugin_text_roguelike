RELIC_CLASS_REGISTRY = {}

def register_relic(relic_id: str):
    def decorator(cls):
        RELIC_CLASS_REGISTRY[relic_id] = cls
        return cls
    return decorator
