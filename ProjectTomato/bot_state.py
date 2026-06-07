import threading
import time
from collections import deque

class BotState:
    """
    Thread-safe shared state container for:
    - CV tracking
    - Movement logic
    - UI (PyQt)
    """

    def __init__(self):
        self._lock = threading.RLock()

        # -------------------------
        # Position tracking
        # -------------------------
        self._player_x = 0
        self._player_y = 0

        self._goal_x = 0
        self._goal_y = 0

        # movement history (for "is moving")
        self.history_size = 8
        self._history = deque([(0, 0)] * self.history_size, maxlen=self.history_size)

        # -------------------------
        # GUI override stop
        # -------------------------
        self._gui_stop = False

        # -------------------------
        # CV / system state
        # -------------------------
        self._is_stopped = False
        self._last_stop_change = time.time()

        self._area = "Burning Cernium"
        self._class = "Hero"
        self._map = ""

        # -------------------------
        # Rune tracking
        # -------------------------

        self._rune_x = 0
        self._rune_y = 0
        
        # Rune state
        self._rune_available = False
        self._last_rune_used_time = 0

        # Stability tracking
        self._rune_candidate_state = False
        self._rune_candidate_start_time = 0

        # Config
        self._rune_confirm_time = 1.0   # seconds needed for consensus
        self._rune_cooldown = 600.0     # 10 minutes

        # event bus (inject this)
        self.bus = None

        # rotation / config sync flag
        self._config_loaded = True

        # used to clear serial queue when area/class swaps
        self._generation = 0

    def set_event_bus(self, bus):
        self.bus = bus

    # =========================================================
    # Player position
    # =========================================================
    def set_player_position(self, x: int, y: int):
        with self._lock:
            self._player_x = x
            self._player_y = y
            self._history.append((x, y))

    def get_player_position(self):
        with self._lock:
            return self._player_x, self._player_y

    # =========================================================
    # Goal position
    # =========================================================
    def set_goal_position(self, x: int, y: int):
        with self._lock:
            self._goal_x = x
            self._goal_y = y

    def get_goal_position(self):
        with self._lock:
            return self._goal_x, self._goal_y

    # =========================================================
    # Movement detection (replaces check_is_moving)
    # =========================================================
    def is_moving(self) -> bool:
        with self._lock:
            if len(self._history) < 2:
                return False

            px, py = self._history[-1]

            for x, y in self._history:
                if abs(x - px) > 1 or abs(y - py) > 1:
                    return True
            return False

    # =========================================================
    # Stop state
    # =========================================================
    def set_gui_stopped(self, value: bool):
        with self._lock:
            self._gui_stop = value

    def is_gui_stopped(self) -> bool:
        with self._lock:
            return self._gui_stop
    
    def set_stopped(self, value: bool):
        with self._lock:
            if self._is_stopped != value:
                self._is_stopped = value
                self._last_stop_change = time.time()
                self.bus.emit("stop_changed", value)

    def is_stopped(self) -> bool:
        with self._lock:
            return self._is_stopped

    def stop_age(self) -> float:
        with self._lock:
            return time.time() - self._last_stop_change

    # =========================================================
    # CV identity (class/area/map)
    # =========================================================
    def set_context(self, area: str, cls: str):
        with self._lock:
            changed = False

            if self._area != area:
                self._area = area
                changed = True

            if self._class != cls:
                self._class = cls
                changed = True

            if changed:
                self._generation += 1

    def get_generation(self):
        with self._lock:
            return self._generation
 
    def get_area(self):
        with self._lock:
            return self._area

    def get_class(self):
        with self._lock:
            return self._class

    def is_loaded(self):
        return bool(self._area or self._class)

    # =========================================================
    # Rune position
    # =========================================================

    def set_rune_position(self, x: int, y: int):
        with self._lock:
            self._rune_x = x
            self._rune_y = y

    def get_rune_position(self):
        with self._lock:
            return self._rune_x, self._rune_y

    # =========================================================
    # Rune state
    # =========================================================
    
    def can_rune_exist(self):
        """Hard cooldown gate"""
        return (time.time() - self._last_rune_used_time) >= self._rune_cooldown

    def get_rune_available(self):
        with self._lock:
            return self._rune_available

    # -------------------------
    # called every frame by CV
    # -------------------------
    def update_rune_observation(self, detected: bool):
        now = time.time()

        with self._lock:
            # cooldown overrides everything
            if not self.can_rune_exist():
                detected = False

            # first observation or state change -> reset timer
            if detected != self._rune_candidate_state:
                self._rune_candidate_state = detected
                self._rune_candidate_start_time = now
                return

            # stable long enough?
            duration = now - self._rune_candidate_start_time

            if duration >= self._rune_confirm_time:
                # state confirmed
                if self._rune_available != detected:
                    self._rune_available = detected

                    # emit events only on transitions
                    if self.bus:
                        if detected:
                            self.bus.emit("rune_detected")
                        else:
                            self.bus.emit("rune_lost")