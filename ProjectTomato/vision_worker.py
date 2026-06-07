# vision_engine.py
import cv2
import numpy as np
import threading
import time
import constants

class VisionWorker(threading.Thread): 
    def __init__(self, state, json_store, frame_state, event_bus, serial):
        super().__init__(daemon=True)
        self.state = state
        self.bus = event_bus
        self.frame_state = frame_state
        self.json = json_store
        self.serial = serial

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
            if not ret:
                print("Failed to grab frame.")
                break

            self.process(frame)

            # SIGNAL: one full loop completed
            with self.lock:
                self.loop_count += 1
                self.loop_complete.set()

            time.sleep(0.03)

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

        # ---- update JSON and set minimap bounds ----
        self.json.load_map(self.state.get_area())
        self.set_minimap_bounds()

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
            self.json.load_class(p_class, area)

            # ONLY push config if class changed
            if class_changed:
                self.push_config()
    
    def set_minimap_bounds(self):
        map_data = self.json.get_map_data()
        offset = map_data.get("mapOffset", {})
        bounds = map_data.get("mapBounds", {})

        mx, my = int(offset.get("x", 0)), int(offset.get("y", 0))
        mw, mh = int(bounds.get("w", 0)), int(bounds.get("h", 0))

        self.frame_state.set_minimap_bounds_yhxw(my, mh, mx, mw)

    def push_config(self):
        setup = self.json.get_setup_info()

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
        stop_template = cv2.imread('lib/Images/Sacred Symbol.png', cv2.IMREAD_GRAYSCALE)
        cv_stop = self.match_image(frame, stop_template, 0.95)
        
        if (self.state.stop_age() >= 3):
            return not cv_stop
        else:
            return self.state.is_stopped()
        
    def detect_class(self, frame):
        return self.compare_image_to_list(frame, self.state.get_class(), constants.class_list)

    def detect_area(self, frame):
        return self.compare_image_to_list(frame, self.state.get_area(), constants.area_list)
    
    # =========================================================
    # Image Recognition and Comparison
    # =========================================================

    # Compares an image to a list of potential class/area images
    def compare_image_to_list(self, frame, name, list):
        if name and name.strip():
            image_path = f'lib/Images/{name}.png'
            template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

            if template is None:
                return name  # or False / fallback

            if not self.match_image(frame, template, 0.90):
                for item in list:
                    path = "".join(['lib/Images/', item, ".png"])     
                    template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                    if self.match_image(frame, template, 0.90):
                        return item                

        return name
    
    def match_image(self, cropped_frame, template, threshold):   
        # Convert frame to grayscale
        gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

        # Apply template matching
        result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # If match is above threshold, draw a rectangle around the found template
        if max_val >= threshold:
            return True
        else:
            return False