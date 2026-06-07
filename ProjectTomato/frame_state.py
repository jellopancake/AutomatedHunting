import threading
import cv2
import time

class FrameState:
    def __init__(self):
        self.lock = threading.Lock()

        # Raw source
        self._raw_frame = None

        # Cropped regions
        self._minimap_frame = None
        self._class_frame = None
        self._area_frame = None
        self._stop_frame = None

        # Processed frames
        self._hsv_minimap = None

        # Debug / display
        self._display_frame = None

        # Frame boundary values
        self._display_frame_height = 220
        self._display_frame_width = 250

        self._minimap_bounds_yhxw = [68, 100, 7, 240]

    def update_state(self, frame):
        self.set_display_frame(frame)
        self.set_class_frame(frame)
        self.set_area_frame(frame) 
        self.set_stop_frame(frame)
        self.set_minimap_frame(frame)
        #self.show_all_frames()

    # =========================================================
    # Computer Vision Controller Frames
    # =========================================================

    def set_raw_frame(self, frame):
        with self.lock:
            self._raw_frame = frame.copy()
        
        self.update_state(frame)

    def set_minimap_frame(self, frame):
        y, h, x, w = self.get_minimap_bounds_yhxw()
        cropped_frame = frame[y: y+h, x: x+w]

        # While setting the minimap frame we convert it to HSV and save it separately for processing
        self.set_hsv_minimap(cropped_frame)
        
        with self.lock:
            self._minimap_frame = cropped_frame.copy()

    def set_class_frame(self, frame):
        frame_height, frame_width = frame.shape[:2]
        frame_y1 = frame_height-83
        frame_y2 = frame_height-45
        frame_x1 = frame_width-38
        frame_x2 = frame_width
        cropped_frame = frame[frame_y1:frame_y2, frame_x1:frame_x2]

        with self.lock:
            self._class_frame = cropped_frame.copy()

    def set_area_frame(self, frame):
        frame_y1 = 26
        frame_y2 = 66
        frame_x1 = 4
        frame_x2 = 44
        cropped_frame = frame[frame_y1:frame_y2, frame_x1:frame_x2]

        with self.lock:
            self._area_frame = cropped_frame.copy()

    def set_stop_frame(self, frame):
        cropped_frame = frame[self._display_frame_height-70 : self._display_frame_height, 0 : 40]

        with self.lock:
            self._stop_frame = cropped_frame.copy()

    def get_raw_frame(self):
        with self.lock:
            return None if self._raw_frame is None else self._raw_frame.copy()

    def get_minimap_frame(self):
        with self.lock:
            return None if self._minimap_frame is None else self._minimap_frame.copy()

    def get_class_frame(self):
        with self.lock:
            return None if self._class_frame is None else self._class_frame.copy()

    def get_area_frame(self):
        with self.lock:
            return None if self._area_frame is None else self._area_frame.copy()

    def get_stop_frame(self):
        with self.lock:
            return None if self._stop_frame is None else self._stop_frame.copy()

    # =========================================================
    # Processed CV Frames
    # =========================================================

    # Getter
    def get_hsv_minimap(self):
        return self._hsv_minimap.copy()

    # Setter
    def set_hsv_minimap(self, frame):
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        self._hsv_minimap = hsv_frame

    # =========================================================
    # GUI Frames
    # =========================================================

    def set_display_frame(self, frame):
        frame_y1 = 0
        frame_y2 = 220
        frame_x1 = 0
        frame_x2 = 250
        cropped_frame = frame[frame_y1:frame_y2, frame_x1:frame_x2]
        with self.lock:
            self._display_frame = cropped_frame.copy()

    def get_display_frame(self):
        with self.lock:
            return None if self._display_frame is None else self._display_frame.copy()
        
    # =========================================================
    # Bounds
    # =========================================================
    
    def set_minimap_bounds_yhxw(self, y=None, h=None, x=None, w=None):
        with self.lock:
            cy, ch, cx, cw = self._minimap_bounds_yhxw

            self._minimap_bounds_yhxw = [
                y if y is not None else cy,
                h if h is not None else ch,
                x if x is not None else cx,
                w if w is not None else cw,
            ]

    def get_minimap_bounds_yhxw(self):
        with self.lock:
            return self._minimap_bounds_yhxw
        
    # =========================================================
    # Debug code
    # =========================================================

    def show_all_frames(self):
        frames = {
            "MINIMAP": self.get_minimap_frame(),
            "HSV": self.get_hsv_minimap(),
            "CLASS": self.get_class_frame(),
            "AREA": self.get_area_frame(),
            "STOP": self.get_stop_frame(),
        }

        for name, frame in frames.items():
            if frame is not None:
                cv2.imshow(name, frame)
                cv2.waitKey(1)
        
        cv2.waitKey(0)