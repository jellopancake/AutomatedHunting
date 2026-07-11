# vision_engine.py
import cv2
import numpy as np
import threading
import time
import constants

class VisionWorker(threading.Thread): 
    def __init__(self, state, config, frame_state, serial):
        super().__init__(daemon=True)
        self.state = state
        self.frame_state = frame_state
        self.config = config
        self.serial = serial

        # ---- Image Templates for CV comparison ----
        self.stop_template = cv2.imread('lib/Images/Sacred Symbol.png', cv2.IMREAD_GRAYSCALE)

        self.class_templates = {
            name: cv2.imread(f'lib/Images/{name}.png', cv2.IMREAD_GRAYSCALE)
            for name in constants.class_list
        }

        self.area_templates = {
            name: cv2.imread(f'lib/Images/{name}.png', cv2.IMREAD_GRAYSCALE)
            for name in constants.area_list
        }

        # ---- Run once before botcontroller check ----
        self.loop_complete = threading.Event()
        self.loop_count = 0
        self.lock = threading.Lock()

        self.running = True

    def run(self):
        capture_index = 0
        cap = cv2.VideoCapture(
            capture_index,
            apiPreference=cv2.CAP_ANY,
            params=[
                cv2.CAP_PROP_FRAME_WIDTH, 1920,
                cv2.CAP_PROP_FRAME_HEIGHT, 1080
            ]
        )

        print("[INFO] Starting CV debug loop... Press Q to quit")

        if not cap.isOpened():
            print("Error: Capture card not detected.")
            return

        while self.running:
            ret, frame = cap.read()

            if not ret or frame is None:
                print("[CV] Frame grab failed, retrying...")
                time.sleep(0.01)
                continue

            # SIGNAL: one full loop completed
            with self.lock:
                self.loop_count += 1
                self.loop_complete.set()

            start = time.time()

            self.process(frame)

            elapsed = time.time() - start
            sleep_time = max(0, 0.03 - elapsed)
            time.sleep(sleep_time)

        cap.release()

    def process(self, frame):        
        self.frame_state.set_raw_frame(frame)

        # ---- stop detection ----
        stop = self.detect_stop(self.frame_state.get_stop_frame())
        self.state.set_stopped(stop)

        if(self.state.is_stopped() != True):
            # ---- player detection ----
            self.find_player(self.frame_state.get_hsv_minimap())

            # ---- rune detection ----
            self.find_rune(self.frame_state.get_hsv_minimap())

        # ---- class detection ----
        p_class = self.detect_class(self.frame_state.get_class_frame())

        # ---- area detection ----
        area = self.detect_area(self.frame_state.get_area_frame())

        self.compare_area_and_class(p_class, area)

    # =========================================================
    # Bot State, Frame State, and Config updates
    # =========================================================
    
    def compare_area_and_class(self, p_class, area):
        current_class = self.state.get_class()
        current_area = self.state.get_area()

        class_changed = (p_class != current_class)
        area_changed = (area != current_area)

        if class_changed or area_changed:
            self.state.set_context(area, p_class)
            self.config.load_class(p_class, area)

            # ONLY push config if class changed
            if class_changed:
                self.push_config()

            # ONLY load new map if area has changed
            if area_changed:
            # ---- update JSON and set minimap bounds ----
                self.config.load_map(self.state.get_area())
                self.set_minimap_bounds()
    
    def set_minimap_bounds(self):
        map_data = self.config.get_map_data()
        offset = map_data.get("mapOffset", {})
        bounds = map_data.get("mapBounds", {})

        mx, my = int(offset.get("x", 0)), int(offset.get("y", 0))
        mw, mh = int(bounds.get("w", 0)), int(bounds.get("h", 0))

        self.frame_state.set_minimap_bounds_yhxw(my, mh, mx, mw)

    def push_config(self):
        setup = self.config.get_setup_info()

        double_jump = setup["doubleJumpDelay"]
        short_double_jump = setup["shortDoubleJumpDelay"]

        # -------------------------
        # Validate inputs first
        # -------------------------
        if double_jump is None or short_double_jump is None:
            print("[CONFIG] Missing delay values, skipping config push")
            return

        # -------------------------
        # Transform
        # -------------------------
        digit1 = round(double_jump / 20)
        digit2 = round((short_double_jump - 60) / 20)

        digit1 = max(0, min(9, digit1))
        digit2 = max(0, min(9, digit2))    

        self.serial.submit_config(str(digit1), str(digit2))

    # =========================================================
    # Player Location Detection
    # =========================================================

    def find_player(self, hsv):
        # ---- player detection ----
        lower_yellow = np.array([25, 150, 200])
        upper_yellow = np.array([35, 220, 255])

        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)

            self.state.set_player_position(x + w // 2, y + h // 2)

    # =========================================================
    # Rune Logic
    # =========================================================

    def find_rune(self, hsv):
        # ---- rune detection ----
        lower_pink = np.array([143, 100, 200])
        upper_pink = np.array([153, 200, 255])

        mask = cv2.inRange(hsv, lower_pink, upper_pink)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            contours_size = w*h
            rune_size = 14

            if (contours_size > rune_size):
                self.state.set_rune_position(x,y)
                
            rune_detected_now = (contours_size > rune_size)
            self.state.update_rune_observation(rune_detected_now)

    # =========================================================
    # Stop, Class, Area Detection
    # =========================================================

    def detect_stop(self, frame):
        cv_stop = self.match_image(frame, self.stop_template, 0.95)
        
        if (self.state.stop_age() >= 3):
            return not cv_stop
        else:
            return self.state.is_stopped()
        
    def detect_class(self, frame):
        return self.compare_image_to_list(
            frame,
            self.state.get_class(),
            constants.class_list,
            self.class_templates
    )

    def detect_area(self, frame):
        return self.compare_image_to_list(
            frame,
            self.state.get_area(),
            constants.area_list,
            self.area_templates
        )
    # =========================================================
    # Image Recognition and Comparison
    # =========================================================

    # Compares an image to a list of potential class/area images
    def compare_image_to_list(self, frame, name, items, template_dict):
        if name and name.strip():
            template = template_dict.get(name)

            if template is None:
                return name

            if not self.match_image(frame, template, 0.90):
                for item in items:
                    template = template_dict.get(item)
                    if template is not None and self.match_image(frame, template, 0.90):
                        return item

        return name
        
    def match_image(self, cropped_frame, template, threshold):
        if cropped_frame is None or template is None:
            return False

        if cropped_frame.size == 0 or template.size == 0:
            return False

        h, w = cropped_frame.shape[:2]
        th, tw = template.shape[:2]

        if th > h or tw > w:
            return False

        gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        return max_val >= threshold