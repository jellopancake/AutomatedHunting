import time
import threading
import cv2

# import your real classes
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

class DummyRotation:
    def __init__(self):
        self.index = 0
        self.rotations = [
            {
                "commands": [
                    {"command": "MOVE", "parameter": "A", "wait": 50},
                    {"command": "ATTACK", "parameter": "B", "wait": 50},
                ]
            }
        ]

    def reload_rotation(self):
        pass

    def get_current(self):
        if self.index >= len(self.rotations):
            return None
        return self.rotations[self.index]

    def next_rotation_step(self):
        self.index += 1


class DummyMovement:
    def move_to_start(self):
        print("[MOVE] move_to_start")

    def reset_servos(self):
        print("[MOVE] reset_servos")


class DummyBus:
    def subscribe(self, event, cb):
        print(f"[BUS] subscribed to {event}")

    def emit(self, event, data=None):
        print(f"[BUS] emit {event}")


# -----------------------------
# INTERACTIVE TEST
# -----------------------------
def run_test():
    PORT = "COM3"
    BAUD = 9600
    
    state = BotState()
    frame_state = FrameState()
    config = ConfigStore()
    bus = EventBus()

    state.set_event_bus(bus)

    serial = SerialCommandExecutor(PORT, BAUD, state)
    rotation = RotationState(config)
    movement = MovementController(serial, state, config)



    # -----------------------------
    # Vision Worker (CV runs in background)
    # -----------------------------
    vision_worker = VisionWorker(state, config, frame_state, bus, serial)
    vision_thread = threading.Thread(
        target=vision_worker.run,
        daemon=True
    )
    vision_thread.start()
    vision_worker.loop_complete.wait()

    movement.reset_servos()

    # -----------------------------
    # Bot Controller (but NOT auto-running)
    # -----------------------------
    bot = BotController(
        state,
        serial,
        rotation,
        movement,
        bus
    )

    print("\n--- TEST READY ---")
    print("Commands:")
    print("  1 = run ONE rotation step")
    print("  v = toggle vision window")
    print("  q = quit\n")

    show_cv = False

    while True:
        key = input(">> ").strip()

        # -----------------------------
        # STEP ROTATION MANUALLY
        # -----------------------------
        if key == "1":
            print("\n[TEST] Running ONE rotation step...\n")
            bot.load_and_run_current_rotation()

        # -----------------------------
        # TOGGLE CV DISPLAY
        # -----------------------------
        elif key == "v":
            show_cv = not show_cv
            print(f"[TEST] CV display = {show_cv}")

        # -----------------------------
        # QUIT
        # -----------------------------
        elif key == "q":
            print("[TEST] shutting down...")
            vision_worker.running = False
            break

        # -----------------------------
        # SHOW CV WINDOWS (optional debug)
        # -----------------------------
        if show_cv:
            # Draw overlays
            display = frame_state.get_display_frame()
            debug_frame = draw_debug(display, state, frame_state)

            cv2.imshow("CV DEBUG VIEW", debug_frame)
            cv2.waitKey(1)

    cv2.destroyAllWindows()

# ---------------------------------------------------
# Overlay drawing
# ---------------------------------------------------
def draw_debug(frame, state: BotState, frame_state: FrameState):
    img = frame.copy()

    # Map offset
    y, h, x, w = frame_state.get_minimap_bounds_yhxw()

    y0 = 20
    dy = 20

    # Player
    px, py = state.get_player_position()
    cv2.circle(img, (px + x, py + y), 6, (0, 255, 0), -1)
    cv2.putText(img, f"Player: ({px},{py})", (10, y0),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Goal
    gx, gy = state.get_goal_position()
    cv2.circle(img, (gx + x, gy + y), 6, (0, 255, 255), -1)
    cv2.putText(img, f"Goal: ({gx},{gy})", (10, y0 + dy),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # Rune
    rx, ry = state.get_rune_position()
    if state.get_rune_available():
        cv2.circle(img, (rx + x, ry + y), 6, (255, 0, 255), -1)
        cv2.putText(img, f"Rune: ({rx},{ry})", (10, y0 + 2*dy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    else:
        cv2.putText(img, "Rune: None", (10, y0 + 2*dy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

    # Context
    cv2.putText(img, f"Area: {state.get_area()}", (10, y0 + 3*dy),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.putText(img, f"Class: {state.get_class()}", (10, y0 + 4*dy),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return img

if __name__ == "__main__":
    run_test()