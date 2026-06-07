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
    bot_state = BotState(bus)

    # =========================================================
    # 3. Hardware Layer
    # =========================================================
    serial_executor = SerialCommandExecutor(3, 9600)

    # =========================================================
    # 4. Movement + Rotation
    # =========================================================
    rotation_state = RotationState(config)
    movement_controller = MovementController(serial_executor, bot_state)

    # =========================================================
    # 5. Bot Controller
    # =========================================================
    bot_controller = BotController(
        state=bot_state,
        serial=serial_executor,
        rotation=rotation_state,
        movement=movement_controller,
        bus=bus,
    )

    # =========================================================
    # 6. Vision Worker (runs in thread)
    # =========================================================
    vision_worker = VisionWorker(
        state=bot_state,
        config=config,
        frame_state=frame_state,
        bus=bus,
    )

    vision_thread = threading.Thread(
        target=vision_worker.run,
        daemon=True
    )

    # =========================================================
    # 7. Bot Loop Thread
    # =========================================================
    bot_thread = threading.Thread(
        target=bot_controller.run,
        daemon=True
    )

    # Start background systems BEFORE GUI
    vision_thread.start()
    bot_thread.start()

    # =========================================================
    # 8. GUI (MUST be main thread)
    # =========================================================
    app = QApplication(sys.argv)

    window = GUI(frame_state, bot_state, bus)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()