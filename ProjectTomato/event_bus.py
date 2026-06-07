import threading

class EventBus:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_type, callback):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def emit(self, event_type, data=None):
        for cb in self.listeners.get(event_type, []):
            def wrapped():
                print(f"[EVENT] {event_type} -> {cb}")
                cb(data)
            threading.Thread(target=wrapped, daemon=True).start()