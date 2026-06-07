import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTextEdit
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer
import threading
from playsound import playsound

class GUI(QWidget):
    def __init__(self, frame_state, bot_state, bus):
        super().__init__()

        self.bus = bus
        self.frame_state = frame_state
        self.bot_state = bot_state

        self.setWindowTitle("Monitor")

        # ---- UI Elements ----
        self.minimap_label = QLabel()
        self.class_label = QLabel()
        self.area_label = QLabel()
        self.stop_label = QLabel()

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFixedHeight(150)

        # ---- Layout ----
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(self.minimap_label)
        frame_layout.addWidget(self.class_label)
        frame_layout.addWidget(self.area_label)
        frame_layout.addWidget(self.stop_label)

        main_layout = QVBoxLayout()
        main_layout.addLayout(frame_layout)
        main_layout.addWidget(self.info_text)

        self.setLayout(main_layout)
        self.setWindowTitle("Monitor")

        # subscribe to events
        self.bus.subscribe("frame_ready", self.update_frame)
        self.bus.subscribe("rune_detected", self.on_rune_detected)
        self.bus.subscribe("stop_changed", self.on_stop_changed)

        # ---- Timer ----
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(30)  # ~30 FPS



    # =========================================================
    # UI UPDATE
    # =========================================================
    def update_ui(self):
        # ---- Frames ----
        minimap = self.frame_state.get_minimap_frame()
        class_frame = self.frame_state.get_class_frame()
        area_frame = self.frame_state.get_area_frame()
        stop_frame = self.frame_state.get_stop_frame()

        # ---- Bot State ----
        player_pos = self.bot_state.get_player_position()
        rune_pos = self.bot_state.get_rune_position()

        is_moving = self.bot_state.is_moving()
        rune_available = self.bot_state.is_rune_available()
        current_class = self.bot_state.get_class()
        current_area = self.bot_state.get_area()

        # ---- Draw overlay on minimap ----
        minimap = self.draw_overlay(minimap)

        # ---- Render Frames ----
        self.set_label_image(self.minimap_label, minimap)
        self.set_label_image(self.class_label, class_frame)
        self.set_label_image(self.area_label, area_frame)
        self.set_label_image(self.stop_label, stop_frame)

        # ---- Update Text Panel ----
        text = f"""
            Player: {player_pos}
            Rune: {rune_pos}

            isMoving: {is_moving}
            runeAvailable: {rune_available}

            Class: {current_class}
            Area: {current_area}
            """
        self.info_text.setText(text)

    # =========================================================
    # DRAW PLAYER / RUNE
    # =========================================================
    def draw_overlay(self, frame):
        frame = frame.copy()

        player = self.bot_state.get_player_position()
        rune = self.bot_state.get_rune_position()

        # player (green)
        if player:
            cv2.circle(frame, player, 5, (0, 255, 0), -1)

        # rune (pink)
        if rune:
            cv2.circle(frame, rune, 5, (0, 255, 255), -1)

        return frame

    # =========================================================
    # IMAGE CONVERSION
    # =========================================================
    def update_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w

        qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_img))

    def on_rune_detected(self, data):
        # non-blocking sound
        threading.Thread(
            target=lambda: playsound("lib/Sounds/Alarm.wav"),
            daemon=True
        ).start()

    def on_stop_changed(self, is_stopped):
        if is_stopped:
            self.setWindowTitle("(Paused)")
        else:
            self.setWindowTitle("(Running)")
