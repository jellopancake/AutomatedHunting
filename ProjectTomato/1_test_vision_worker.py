import cv2
import numpy as np
import threading
import time

from vision_worker import VisionWorker
from frame_state import FrameState
from bot_state import BotState
from config_store import ConfigStore
from event_bus import EventBus
from serial_command_executor import SerialCommandExecutor

# ---------------------------------------------------
# Overlay drawing
# ---------------------------------------------------
def draw_debug(frame, state: BotState, frame_state: FrameState):
    img = frame.copy()

    # Map offset
    y, h, x, w = frame_state.get_minimap_bounds_yhxw()

    # Player
    px, py = state.get_player_position()
    cv2.circle(img, (px + x, py + y), 6, (0, 255, 0), -1)
    cv2.putText(img, f"Player: ({px},{py})", (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Rune
    rx, ry = state.get_rune_position()
    if state.get_rune_available():
        cv2.circle(img, (rx + x, ry + y), 6, (255, 0, 255), -1)
        cv2.putText(img, f"Rune: ({rx},{ry})", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    else:
        cv2.putText(img, "Rune: None", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

    # Context
    cv2.putText(img, f"Area: {state.get_area()}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.putText(img, f"Class: {state.get_class()}", (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.putText(img, f"Moving: {state.is_moving()}", (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return img

# ---------------------------------------------------
# MAIN TEST LOOP
# ---------------------------------------------------
def run_cv_debug():
    PORT = "COM3"
    BAUD = 9600
    
    state = BotState()
    frame_state = FrameState()
    config = ConfigStore()
    bus = EventBus()
    state.set_event_bus(bus)
    serial = SerialCommandExecutor(PORT, BAUD, state)

    worker = VisionWorker(state, config, frame_state, serial)

    capture_index = 0
    cap = cv2.VideoCapture(capture_index, apiPreference=cv2.CAP_ANY, params=[
        cv2.CAP_PROP_FRAME_WIDTH, 1920,
        cv2.CAP_PROP_FRAME_HEIGHT, 1080])

    print("[INFO] Starting CV debug loop... Press Q to quit")

    if not cap.isOpened():
        print("Error: Capture card not detected.")
    else:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break
            
            # Run full pipeline manually (important for debug control)
            worker.process(frame)
            
            # Draw overlays
            display = frame_state.get_display_frame()
            debug_frame = draw_debug(display, state, frame_state)

            cv2.imshow("CV DEBUG VIEW", debug_frame)

            # Also show minimap crop
            minimap = frame_state.get_minimap_frame()
            if minimap is not None:
                cv2.imshow("MINIMAP", minimap)

            # Also show minimap hsv
            hsv = frame_state.get_hsv_minimap()
            if minimap is not None:
                cv2.imshow("HSV", hsv)

            # Show class frame
            class_frame = frame_state.get_class_frame()
            if class_frame is not None:
                cv2.imshow("CLASS", class_frame)

            # Show area frame
            area_frame = frame_state.get_area_frame()
            if area_frame is not None:
                cv2.imshow("AREA", area_frame)

            # Show stop frame
            stop_frame = frame_state.get_stop_frame()
            if stop_frame is not None:
                cv2.imshow("STOP", stop_frame)

            # Print live state
            print(
                f"AREA={state.get_area()} | CLASS={state.get_class()} | "
                f"PLAYER={state.get_player_position()} | "
                f"RUNE={state.get_rune_position()} | "
                f"AVAILABLE={state.get_rune_available()}",
                end="\r"
            )

            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                break

            time.sleep(0.03)

        cap.release()
    cv2.destroyAllWindows()


# ---------------------------------------------------
# RUN LIKE A TEST
# ---------------------------------------------------
if __name__ == "__main__":
    run_cv_debug()