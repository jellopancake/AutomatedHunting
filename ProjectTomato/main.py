import sys
import threading

from PyQt6.QtWidgets import QApplication

# ---- Core ----
from event_bus import EventBus
from config_store import ConfigStore
from frame_state import FrameState

# ---- Bot ----
from bot_state import BotState
from bot_controller import BotController
from movement_controller import MovementController
from rotation_state import RotationState

# ---- Vision ----
from vision_worker import VisionWorker

# ---- Hardware ----
from serial_command_executor import SerialCommandExecutor

# ---- GUI ----
from GUI import GUI


def main():
    # =========================================================
    # 1. Core Systems
    # =========================================================
    bus = EventBus()
    config = ConfigStore()
    frame_state = FrameState()

    # =========================================================
    # 2. Bot State
    # =========================================================
    state = BotState()
    state.set_event_bus(bus)

    # =========================================================
    # 3. Hardware Layer
    # =========================================================
    PORT = "COM3"
    BAUD = 9600
    serial_executor = SerialCommandExecutor(PORT, BAUD, state)

    # =========================================================
    # 4. Movement + Rotation
    # =========================================================
    rotation = RotationState(config)
    movement_controller = MovementController(serial_executor, state, config)

    # =========================================================
    # 5. Bot Controller
    # =========================================================
    bot_controller = BotController(
        state=state,
        serial=serial_executor,
        rotation=rotation,
        movement_controller=movement_controller
    )

    # =========================================================
    # 6. Vision Worker (runs in thread)
    # =========================================================
    vision_worker = VisionWorker(
        state=state,
        config=config,
        frame_state=frame_state,
        serial=serial_executor
    )

    vision_thread = threading.Thread(
        target=vision_worker.run,
        daemon=True
    )

    # Start background systems BEFORE GUI
    vision_thread.start()
    vision_worker.loop_complete.wait()

    bot_controller.start()

    # =========================================================
    # 8. GUI (MUST be main thread)
    # =========================================================
    app = QApplication(sys.argv)

    window = GUI(frame_state, state, rotation, bus)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()