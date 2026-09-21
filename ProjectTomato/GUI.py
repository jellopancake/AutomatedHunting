import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QSizePolicy
)
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import threading
import textwrap
from playsound import playsound

class GUI(QWidget):
    gui_message_signal = pyqtSignal(str)

    def __init__(self, frame_state, state, rotation, bus):
        super().__init__()

        self.bus = bus
        self.frame_state = frame_state
        self.state = state
        self.rotation = rotation

        self.setWindowTitle("Monitor")
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.gui_message_signal.connect(self.display_gui_message)
        self.gui_paused = False

        # ---- UI Elements ----
        self.display_label = QLabel()
        self.display_label.setMinimumSize(300, 300)
        self.display_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.class_label = QLabel()
        self.area_label = QLabel()
        self.stop_label = QLabel()

        self.state_text = QTextEdit()
        self.state_text.setReadOnly(True)
        self.state_text.setFont(QFont("Consolas", 12))
        self.state_text.setFixedHeight(200)

        for lbl in (self.class_label, self.area_label, self.stop_label):
            lbl.setFixedSize(70, 70)  # slightly bigger than 40 for padding
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFixedHeight(140)
        self.info_text.setFont(QFont("Consolas", 12))

        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)
        self.message_text.setFont(QFont("Consolas", 10))

        # ---- Buttons ----
        self.pause_button = QPushButton("Pause")
        self.prev_button = QPushButton("Prev Step")
        self.step_button = QPushButton("Next Step")

        self.pause_button.clicked.connect(self.toggle_pause)
        self.prev_button.clicked.connect(self.prev_step)
        self.step_button.clicked.connect(self.next_step)

        # ==========================================
        # Top: Minimap + Class/Area/Stop
        # ==========================================
        top_layout = QHBoxLayout()

        # Minimap
        top_layout.addWidget(self.display_label, 4)

        # Right side
        right_layout = QVBoxLayout()

        # Class / Area / Stop to the right of minimap
        mini_layout = QHBoxLayout()
        mini_layout.addWidget(self.class_label)
        mini_layout.addWidget(self.area_label)
        mini_layout.addWidget(self.stop_label)

        mini_layout.setSpacing(10)
        mini_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout.addLayout(mini_layout)
        # Text underneath the images
        right_layout.addWidget(self.state_text)

        top_layout.addLayout(right_layout, 2)


        # ==========================================
        # Bottom: Status + Event Messages
        # ==========================================

        bottom_layout = QHBoxLayout()

        bottom_layout.addWidget(self.info_text, 1)
        bottom_layout.addWidget(self.message_text, 3)


        # ==========================================
        # Main Layout
        # ==========================================

        main_layout = QVBoxLayout()

        main_layout.addLayout(top_layout, 4)
        main_layout.addLayout(bottom_layout, 1)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.step_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("Monitor")

        self.setStyleSheet("""
        QWidget {
            background-color: #121212;
            color: #EAEAEA;
        }

        QTextEdit {
            background-color: #0F0F0F;
            color: #00FF9C;
            font-family: Consolas;
            border: 1px solid #222;
        }

        QLabel {
            color: #EAEAEA;
            background-color: transparent;
        }

        QPushButton {
            background-color: #2A2A2A;
            color: #EAEAEA;
            border: 1px solid #333;
            padding: 6px;
            border-radius: 6px;
        }

        QPushButton:hover {
            background-color: #3A3A3A;
        }

        QPushButton:pressed {
            background-color: #505050;
        }
        """)

        self.setAutoFillBackground(True)

        # subscribe to events
        self.bus.subscribe("rune_detected", self.on_rune_detected)
        self.bus.subscribe("gui_message", self.on_gui_message)

        # ---- Timer ----
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(30)  # ~30 FPS

    # =========================================================
    # BUTTONS
    # =========================================================

    def toggle_pause(self):
        self.gui_paused = not self.gui_paused
        self.state.set_gui_stopped(self.gui_paused)
        self.pause_button.setText("Resume" if self.gui_paused else "Pause")

    def prev_step(self):
        if not (self.state.is_stopped() or self.state.is_gui_stopped()):
            return    
        self.rotation.prev_rotation_step()

    def next_step(self):
        if not (self.state.is_stopped() or self.state.is_gui_stopped()):
            return    
        self.rotation.next_rotation_step()

    # =========================================================
    # UI UPDATE
    # =========================================================
    def update_ui(self):
        # ---- Frames ----
        display = self.frame_state.get_display_frame()

        class_frame = self.frame_state.get_class_frame()
        area_frame = self.frame_state.get_area_frame()
        stop_frame = self.frame_state.get_stop_frame()

        self.set_label_image(self.class_label, class_frame)
        self.set_label_image(self.area_label, area_frame)
        self.set_label_image(self.stop_label, stop_frame)


        # ---- Bot State ----
        player_pos = self.state.get_player_position()
        rune_pos = self.state.get_rune_position()
        is_stopped = self.state.is_stopped()
        is_gui_stopped = self.state.is_gui_stopped()
        is_moving = self.state.is_moving()
        rune_available = self.state.get_rune_available()

        rotation_index = self.rotation.get_rotation_index()
        current_class = self.state.get_class()
        current_area = self.state.get_area()

        generation = self.state.get_generation()
        is_queue_empty = self.state.is_queue_empty()

        # ---- Draw overlay on display frame ----
        display = self.draw_overlay(display)

        # ---- Render Frames ----
        self.set_label_image(self.display_label, display)

        # ---- Update Top Right Text Panel ----

        state_text = textwrap.dedent(f"""
            Class: {current_class}
            Area: {current_area}
            STOPPED: {is_stopped}
        """).strip()

        self.state_text.setText(state_text)

        # ---- Update Bottom Left Text Panel ----
        text = textwrap.dedent(f"""
            STOPPED: {is_stopped}
            GUI STOPPED: {is_gui_stopped}
            
            Player: {player_pos}
            Rune: {rune_pos}
            Rotation Index: {rotation_index}

            isMoving: {is_moving}
            runeAvailable: {rune_available}
            Generation: {generation}
            Queue Empty: {is_queue_empty}
            """).strip()
        self.info_text.setText(text)

        doc_height = self.info_text.document().size().height()
        self.info_text.setFixedHeight(int(doc_height + 10))

    # =========================================================
    # DRAW PLAYER / RUNE
    # =========================================================
    def draw_overlay(self, frame):
        img = frame.copy()

        # Map offset
        y, h, x, w = self.frame_state.get_minimap_bounds_yhxw()

        # Player
        px, py = self.state.get_player_position()
        cv2.circle(img, (px + x, py + y), 4, (0, 255, 0), -1)

        # Goal
        gx, gy = self.state.get_goal_position()
        base_x, base_y = gx + x, gy + y + 5

        cv2.line(img, (base_x, base_y), (base_x, base_y - 10), (0, 0, 255), 1)

        # flag triangle
        flag_pts = np.array([
            (base_x, base_y - 10),
            (base_x + 7, base_y - 8),
            (base_x, base_y - 6)
        ], np.int32)
        cv2.fillPoly(img, [flag_pts], (0, 0, 255))

        # Rune
        rx, ry = self.state.get_rune_position()
        if self.state.get_rune_available():
            cx, cy = rx + x, ry + y

            diamond_pts = np.array([
                (cx, cy - 5),   # top
                (cx + 5, cy),   # right
                (cx, cy + 5),   # bottom
                (cx - 5, cy)    # left
            ], np.int32)

            cv2.fillPoly(img, [diamond_pts], (255, 0, 255))

        return img

    # =========================================================
    # IMAGE CONVERSION
    # =========================================================
    def set_label_image(self, label, frame):
        if frame is None:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb.shape
        bytes_per_line = ch * w

        qt_img = QImage(
            rgb.data,
            w,
            h,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )

        pixmap = QPixmap.fromImage(qt_img)

        label.setPixmap(
            pixmap.scaled(
                label.width(),
                label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    # =========================================================
    # RUNE
    # =========================================================

    def on_rune_detected(self, data=None):
        # non-blocking sound
        threading.Thread(
            target=lambda: playsound("lib/Sounds/Alarm.wav"),
            daemon=True
        ).start()

         # Add message to event log
        self.gui_message_signal.emit("[RUNE] Rune spawned!")

    # =========================================================
    # TEXT WINDOW
    # =========================================================

    def on_gui_message(self, message):
        self.gui_message_signal.emit(message)

    def display_gui_message(self, message):
        self.message_text.append(message)

        # Keep only the most recent 100 messages
        document = self.message_text.document()

        while document.blockCount() > 100:
            cursor = self.message_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

        # Scroll to the newest message
        self.message_text.verticalScrollBar().setValue(
            self.message_text.verticalScrollBar().maximum()
        )