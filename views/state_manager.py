class AppState:
    _is_llm_ready = False
    _listeners = []

    @classmethod
    def set_ready(cls, status: bool):
        cls._is_llm_ready = status
        if status:
            for callback in cls._listeners:
                callback()

    @classmethod
    def is_ready(cls):
        return cls._is_llm_ready

    @classmethod
    def subscribe(cls, callback):
        cls._listeners.append(callback)