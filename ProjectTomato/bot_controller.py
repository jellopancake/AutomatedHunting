import threading
import time
from queue import Queue


class BotController:
    """
    Central orchestrator:
    - reads BotState
    - runs rotation logic
    - sends commands to SerialExecutor
    - reacts to EventBus signals
    """

    def __init__(self, state, serial, rotation, movement_controller):
        self.state = state
        self.serial = serial
        self.rotation = rotation
        self.movement = movement_controller

        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        # internal control flags
        self._stop_requested = False
        self._last_reset_time = 0
        self._reset_interval = 5.0

    # -----------------------------
    # START / STOP
    # -----------------------------
    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self):
        with self._lock:
            self._stop_requested = True

        self._running = False

    # -----------------------------
    # MAIN LOOP
    # -----------------------------
    def run(self):
        while self._running:
            # hard stop
            if self._stop_requested:
                break

            # pause from CV / GUI
            if self.state.is_stopped() or self.state.is_gui_stopped():
                now = time.time()

                if now - self._last_reset_time >= self._reset_interval:
                    self.movement.reset_servos()
                    self._last_reset_time = now

                time.sleep(0.1)  # small yield, NOT blocking delay
                continue

            # If config is empty, CV still needs to provide data
            if not self.state.is_loaded():
                time.sleep(1)
                continue
            
            self.load_and_run_current_rotation()            

        self._shutdown()

    # -----------------------------
    # ROTATION EXECUTION
    # -----------------------------

    def load_and_run_current_rotation(self):
        self.rotation.reload_rotation()
        #self.debug_rotation_info()
        self._execute_current_rotation()


    def debug_rotation_info(self):
        #print(self.rotation.rotation)
        print(self.rotation.get_current())

    def _execute_current_rotation(self):
        rotation_step = self.rotation.get_current()
        if not rotation_step:
            return

        self.movement.move_to_start(rotation_step)
        self._wait()

        # --- check if goal reached ---
        if not self.movement.is_at_goal():
            return  # skip commands AND don't advance rotation

        commands = rotation_step.get("commands", [])

        for cmd_step in commands:
            if self._should_interrupt():
                self.movement.reset_servos()
                return

            cmd = cmd_step.get("command")
            param = str(cmd_step.get("parameter"))
            wait = int(cmd_step.get("wait"))

            self.movement._send(cmd, param, wait)
            
        self._wait()
        self.rotation.next_rotation_step()
    # -----------------------------
    # MOVEMENT / STATE CHECKS
    # -----------------------------
    def _should_interrupt(self):
        return (
            self.state.is_stopped()
            or self.state.is_gui_stopped()
            or self._stop_requested
        )

    # =========================
    # Timing (non-blocking safe)
    # =========================
    def _wait(self, timeout = 30):
        start = time.time()

        while (time.time() - start) < timeout:
            if self.state.is_stopped() or self.state.is_gui_stopped() or self.state.is_queue_empty():
                return
            time.sleep(0.01)

    # -----------------------------
    # CLEANUP
    # -----------------------------
    def _shutdown(self):
        self.movement.reset_servos()