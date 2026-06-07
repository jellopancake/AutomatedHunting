import time
import math
import copy
import threading

class RotationState:
    def __init__(self, config):
        """
        state: BotState (wraps CV info)
        config: ConfigStore (wraps jsonReader)
        """
        self.config = config
        self._lock = threading.RLock()

        self._last_rotations = None
        self.rotation = []
        self.rotation_index = 0
        self.step_count = 0

        self._running = True

    # -------------------------
    # Rotation main functions
    # -------------------------

    def get_current(self):
        with self._lock:
            if not self.rotation:
                return None
            return copy.deepcopy(self.rotation[self.rotation_index])

    # -------------------------
    # Rotation index adjusters
    # -------------------------

    def next_rotation_step(self):
        if self.step_count == 0:
            return

        with self._lock:
            self.rotation_index = (self.rotation_index + 1) % self.step_count

    def previous_rotation_step(self):
        if self.step_count == 0:
            return

        with self._lock:
            self.rotation_index = (self.rotation_index - 1) % self.step_count

    def reset_rotation_index(self):
        with self._lock:
            self.rotation_index = 0

    def get_rotation_index(self):
        with self._lock:
            return self.rotation_index + 1
        
    def get_step_count(self):
        with self._lock:
            return self.step_count

    # -------------------------
    # Rotation loading
    # -------------------------
    def reload_rotation(self):
        rotations = self.config.get_rotation_data() or {}

        if rotations == self._last_rotations:
            return

        self._last_rotations = rotations

        self.step_count = rotations.get("Steps", 1)

        self.rotation = [
            rotations.get(f"Rotation {i}", {})
            for i in range(1, self.step_count + 1)
        ]

        self.reset_rotation_index()
