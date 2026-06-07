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

    def __init__(self, state, serial_executor, rotation_controller, movement_controller, bus):
        self.state = state
        self.serial = serial_executor
        self.rotation = rotation_controller
        self.movement = movement_controller
        self.bus = bus

        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        # internal control flags
        self._paused = False
        self._stop_requested = False

        # subscribe to events
        self._bind_events()

    # -----------------------------
    # EVENT BINDING
    # -----------------------------
    def _bind_events(self):
        self.bus.subscribe("stop_changed", self._on_stop_changed)

    def _on_stop_changed(self, is_stopped: bool):
        with self._lock:
            self._paused = is_stopped

    # -----------------------------
    # START / STOP
    # -----------------------------
    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        with self._lock:
            self._stop_requested = True

        self._running = False

    # -----------------------------
    # MAIN LOOP
    # -----------------------------
    def _loop(self):
        while self._running:
            # hard stop
            if self._stop_requested:
                break

            # pause from CV / GUI
            if self._paused or self.state.is_stopped():
                self.movement.reset_servos()
                time.sleep(0.5)
                continue

            # If config is empty, CV still needs to provide data
            if not self.state.is_loaded():
                time.sleep(1)
                continue
            
            self.load_and_run_current_rotation()            

            time.sleep(0.05)

        self._shutdown()

    # -----------------------------
    # ROTATION EXECUTION
    # -----------------------------

    def load_and_run_current_rotation(self):
        self.rotation.reload_rotation()
        #self.debug_rotation_info()
        self._execute_current_rotation()
        self.rotation.next_rotation_step()

    def debug_rotation_info(self):
        #print(self.rotation.rotation)
        print(self.rotation.get_current())

    def _execute_current_rotation(self):
        rotation_step = self.rotation.get_current()
        if not rotation_step:
            return

        self.movement.move_to_start(rotation_step)

        commands = rotation_step.get("commands", [])

        for cmd_step in commands:

            if self._should_interrupt():
                self.movement.reset_servos()
                return

            cmd = cmd_step.get("command")
            param = str(cmd_step.get("parameter"))
            wait = int(cmd_step.get("wait"))

            self.movement._send(cmd, param, wait)

    # -----------------------------
    # MOVEMENT / STATE CHECKS
    # -----------------------------
    def _should_interrupt(self):
        return (
            self.state.is_stopped()
            or self.state.is_gui_stopped()
            or self._stop_requested 
            or self._paused
        )

    # -----------------------------
    # CLEANUP
    # -----------------------------
    def _shutdown(self):
        self.serial.reset_servos()