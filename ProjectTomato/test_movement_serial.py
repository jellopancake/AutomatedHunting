import time

from movement_controller import MovementController
from serial_command_executor import SerialCommandExecutor
from bot_state import BotState 
from config_store import ConfigStore

# =========================================================
# Minimal Config stub (required by MovementController)
# =========================================================
class TestConfig:
    def get_setup(self):
        return {
            "horizontalMovement": "Flashjump",
            "horizontalMovementDistance": 20,
            "walkMultiplier": 0.05,
            "verticalMovement": "Teleport",
        }

# =========================================================
# Run sequence
# =========================================================
def main():
    # CHANGE THIS to your actual COM port
    PORT = "COM3"
    BAUD = 9600    
    state = BotState()
    serial = SerialCommandExecutor(PORT, BAUD, state)
    config = ConfigStore()
    mc = MovementController(serial, state, config)

    print("\n=== TEST START ===")

    print("\n-> Jump")
    mc.jump()

    time.sleep(3)

    print("\n-> Start Walk RIGHT")
    mc.start_walk("Right")

    time.sleep(3)

    print("\n-> End Walk RIGHT")
    mc.end_walk("Right")

    time.sleep(1)

    print("\n=== TEST COMPLETE ===")

    serial.stop()


if __name__ == "__main__":
    main()