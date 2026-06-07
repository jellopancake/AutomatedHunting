import ujson
import threading
import copy
import constants

class ConfigStore:
    """
    Thread-safe immutable configuration store.
    Loads JSON and exposes read-only snapshots.
    """

    def __init__(self):
        self._lock = threading.RLock()

        self._map_data = {}
        self._rotation_data = {}
        self._setup_info = {}

        self._class_key = ""
        self._area_key = ""
        self._loaded_map = ""

    # -----------------------------
    # LOAD MAP DATA
    # -----------------------------
    def load_map(self, area_choice: str):
        with self._lock:
            with open("lib/JSON/Maps.json", "r") as f:
                raw = ujson.load(f)

            area_data = raw.get(area_choice, {})
            map_key = constants.favourite_map_key.get(area_choice)

            self._map_data = area_data.get(map_key, {})

    # -----------------------------
    # LOAD CLASS DATA
    # -----------------------------
    def load_class(self, class_choice: str, area_choice: str):
        with self._lock:
            map_key = constants.favourite_map_key.get(area_choice)

            with open(f"lib/JSON/Classes/{class_choice}.json", "r") as f:
                raw = ujson.load(f)

            self._setup_info = {
                k: raw.get(k)
                for k in [
                    "className",
                    "doubleJumpDelay",
                    "shortDoubleJumpDelay",
                    "walkMultiplier",
                    "horizontalMovementDistance",
                    "horizontalMovement",
                    "verticalMovement"
                ]
            }

            rotation_root = raw.get("mobbingRotations", {})
            area_data = rotation_root.get(area_choice, {})

            self._rotation_data = area_data.get(map_key, {})

            self._area_key = area_data.get("Area Name", "")
            self._class_key = raw.get("className", "")
            self._loaded_map = map_key
        
        self.load_map(self._area_key)

    # -----------------------------
    # READ ACCESSORS (SAFE COPIES)
    # -----------------------------
    def get_map_data(self):
        with self._lock:
            return copy.deepcopy(self._map_data)

    def get_rotation_data(self):
        with self._lock:
            return copy.deepcopy(self._rotation_data)

    def get_setup_info(self):
        with self._lock:
            return copy.deepcopy(self._setup_info)

    def get_class_key(self):
        with self._lock:
            return self._class_key

    def get_area_key(self):
        with self._lock:
            return self._area_key

    def get_loaded_map(self):
        with self._lock:
            return self._loaded_map