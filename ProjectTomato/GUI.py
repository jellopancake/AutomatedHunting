import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QSizePolicy, QGridLayout, QSlider
)
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import threading
import textwrap
from playsound import playsound
import time

class GUI(QWidget):
    gui_message_signal = pyqtSignal(str)

    def __init__(self, frame_state, state, rotation, bus, vision_worker):
        super().__init__()

        self.bus = bus
        self.frame_state = frame_state
        self.state = state
        self.rotation = rotation
        self.vision_worker = vision_worker

        self.cv_adjustment_mode = False

        self.setWindowTitle("Monitor")
        self.resize(800, 600)
        self.setMinimumSize(800, 600)

        self.normal_ui_widget = QWidget()
        self.cv_adjustment_widget = QWidget()

        self.setup_main_ui()
        self.setup_CV_ui()

        # ==========================================
        # Main Window Layout
        # ==========================================
        window_layout = QVBoxLayout()

        window_layout.addWidget(self.normal_ui_widget)
        window_layout.addWidget(self.cv_adjustment_widget)

        self.setLayout(window_layout)

        self.cv_adjustment_widget.hide()

        # subscribe to events
        self.bus.subscribe("rune_detected", self.on_rune_detected)
        self.bus.subscribe("gui_message", self.on_gui_message)

        # ---- Timer ----
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(30)  # ~30 FPS

    def closeEvent(self, event):
        self.state.set_gui_stopped(True)
        time.sleep(2)

        self.bot_controller.stop()

        self.vision_worker.stop()
        self.vision_worker.join(timeout=2)

        self.serial_executor.stop()

        event.accept()

    # =========================================================
    # UI UPDATE
    # =========================================================
    def update_ui(self):
        if self.cv_adjustment_mode:
            self.update_cv_ui()
        else:
            self.update_main_ui()

    # ======================================================================================
    # MAIN GUI
    # ======================================================================================

    def setup_main_ui(self):
        self.gui_message_signal.connect(self.display_gui_message)
        self.gui_paused = False

        # ---- UI Elements ----
        # Minimap frame
        self.display_label = QLabel()
        self.display_label.setMinimumSize(300, 300)
        self.display_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Class, Area, Stop frames
        self.class_label = QLabel()
        self.area_label = QLabel()
        self.stop_label = QLabel()

        # Minimap CV toggle
        self.cv_adjust_button = QPushButton("CV")
        self.cv_adjust_button.setCheckable(True)
        self.cv_adjust_button.clicked.connect(self.enter_cv_adjustment)

        self.state_text = QTextEdit()
        self.state_text.setReadOnly(True)
        self.state_text.setFont(QFont("Consolas", 12))

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
        self.next_button = QPushButton("Next Step")

        self.pause_button.clicked.connect(self.toggle_pause)
        self.prev_button.clicked.connect(self.prev_step)
        self.next_button.clicked.connect(self.next_step)

        self.pause_button.setMinimumHeight(50)
        self.prev_button.setMinimumHeight(50)
        self.next_button.setMinimumHeight(50)

        # ==========================================
        # Top: Minimap + Class/Area/Stop
        # ==========================================
        top_layout = QHBoxLayout()

        # LEFT SIDE
        # Minimap
        top_layout.addWidget(self.display_label, 4)

        # RIGHT SIDE
        right_layout = QVBoxLayout()

        # Class / Area / Stop to the right of minimap
        mini_layout = QHBoxLayout()
        mini_layout.addWidget(self.class_label)
        mini_layout.addWidget(self.area_label)
        mini_layout.addWidget(self.stop_label)

        top_right_layout = QVBoxLayout()

        top_right_layout.addWidget(self.cv_adjust_button)
        top_right_layout.addStretch()

        mini_layout.addStretch()
        mini_layout.addLayout(top_right_layout)

        mini_layout.setSpacing(10)
        mini_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout.addLayout(mini_layout)

        # Text underneath the images
        right_layout.addWidget(self.state_text)

        top_layout.addLayout(right_layout, 2)

        # Last rune position

        rune_title = QLabel("Last Rune Position")
        rune_title.setFont(QFont("Consolas", 11))
        rune_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ---- Last Rune Position Grid ----
        self.rune_grid = QGridLayout()
        self.rune_grid.setSpacing(0)

        self.rune_cells = []

        for row in range(3):
            for col in range(6):
                cell = QLabel()
                cell.setFixedHeight(40)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)

                cell.setStyleSheet("""
                    QLabel {
                        background-color: #252525;
                        border: 1px solid #444;
                        border-radius: 3px;
                    }
                """)

                self.rune_grid.addWidget(cell, row, col)
                self.rune_cells.append(cell)

        right_layout.addWidget(rune_title)
        right_layout.addLayout(self.rune_grid)

        # ==========================================
        # Bottom: Status + Event Messages
        # ==========================================

        bottom_layout = QHBoxLayout()

        bottom_layout.addWidget(self.info_text, 1)
        bottom_layout.addWidget(self.message_text, 3)


        # ==========================================
        # Main Layout
        # ==========================================

        main_layout = QVBoxLayout(self.normal_ui_widget)

        main_layout.addLayout(top_layout, 4)
        main_layout.addLayout(bottom_layout, 1)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)

        main_layout.addLayout(button_layout)

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
            font-size: 16px;
        }

        QPushButton:hover {
            background-color: #3A3A3A;
        }

        QPushButton:pressed {
            background-color: #505050;
        }
        """)

        self.setAutoFillBackground(True)
    
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
    # MAIN UI UPDATE
    # =========================================================
    def update_main_ui(self):
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
        rune_cardinal_location = self.state.get_rune_cardinal_location()

        # ---- Draw overlay on display frame ----
        display = self.draw_overlay(display)

        # ---- Update rune positioning grid ----
        self.update_rune_grid(rune_cardinal_location)

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

    def update_rune_grid(self, location):
        # Reset all cells
        for cell in self.rune_cells:
            cell.setStyleSheet("""
                QLabel {
                    background-color: #252525;
                    border: 1px solid #444;
                    border-radius: 3px;
                }
            """)

        if location < 1:
            return

        # locations are from 0 - 18
        index = location-1

        if index is None:
            return

        self.rune_cells[index].setStyleSheet("""
            QLabel {
                background-color: #D050D0;
                border: 2px solid #FF80FF;
                border-radius: 3px;
            }
        """)

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

    # ======================================================================================
    # CV GUI
    # ======================================================================================

    def setup_CV_ui(self):
        self.player_mask_label = QLabel()
        self.player_mask_label.setMinimumSize(200, 200)
        self.player_mask_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.player_mask_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.rune_mask_label = QLabel()
        self.rune_mask_label.setMinimumSize(200, 200)
        self.rune_mask_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.rune_mask_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ---- Player Mask Sliders ----
        player_lower, player_upper = self.vision_worker.get_player_hsv()

        self.player_h_min_label, self.player_h_min = \
            self.create_hsv_slider("H Min", 0, 179, player_lower[0])

        self.player_h_max_label, self.player_h_max = \
            self.create_hsv_slider("H Max", 0, 179, player_upper[0])

        self.player_s_min_label, self.player_s_min = \
            self.create_hsv_slider("S Min", 0, 255, player_lower[1])

        self.player_s_max_label, self.player_s_max = \
            self.create_hsv_slider("S Max", 0, 255, player_upper[1])

        self.player_v_min_label, self.player_v_min = \
            self.create_hsv_slider("V Min", 0, 255, player_lower[2])

        self.player_v_max_label, self.player_v_max = \
            self.create_hsv_slider("V Max", 0, 255, player_upper[2])

        # ---- Rune Mask Sliders ----
        rune_lower, rune_upper = self.vision_worker.get_rune_hsv()

        self.rune_h_min_label, self.rune_h_min = \
            self.create_hsv_slider("H Min", 0, 179, rune_lower[0])

        self.rune_h_max_label, self.rune_h_max = \
            self.create_hsv_slider("H Max", 0, 179, rune_upper[0])

        self.rune_s_min_label, self.rune_s_min = \
            self.create_hsv_slider("S Min", 0, 255, rune_lower[1])

        self.rune_s_max_label, self.rune_s_max = \
            self.create_hsv_slider("S Max", 0, 255, rune_upper[1])

        self.rune_v_min_label, self.rune_v_min = \
            self.create_hsv_slider("V Min", 0, 255, rune_lower[2])

        self.rune_v_max_label, self.rune_v_max = \
            self.create_hsv_slider("V Max", 0, 255, rune_upper[2])

        # Player HSV updates
        self.player_h_min.valueChanged.connect(self.update_player_hsv)
        self.player_h_max.valueChanged.connect(self.update_player_hsv)
        self.player_s_min.valueChanged.connect(self.update_player_hsv)
        self.player_s_max.valueChanged.connect(self.update_player_hsv)
        self.player_v_min.valueChanged.connect(self.update_player_hsv)
        self.player_v_max.valueChanged.connect(self.update_player_hsv)

        # Rune HSV updates
        self.rune_h_min.valueChanged.connect(self.update_rune_hsv)
        self.rune_h_max.valueChanged.connect(self.update_rune_hsv)
        self.rune_s_min.valueChanged.connect(self.update_rune_hsv)
        self.rune_s_max.valueChanged.connect(self.update_rune_hsv)
        self.rune_v_min.valueChanged.connect(self.update_rune_hsv)
        self.rune_v_max.valueChanged.connect(self.update_rune_hsv)

        # Return button
        self.cv_return_button = QPushButton("Back")
        self.cv_return_button.clicked.connect(self.exit_cv_adjustment)

        # Contour Size Labels
        self.player_contour_label = QLabel("Player Contour: 0")
        self.rune_contour_label = QLabel("Rune Contour: 0")

        # Reset CV masks to defaults
        self.cv_player_reset_button = QPushButton("Reset Player Defaults")
        self.cv_player_reset_button.clicked.connect(self.reset_cv_player_defaults)

        self.cv_rune_reset_button = QPushButton("Reset Rune Defaults")
        self.cv_rune_reset_button.clicked.connect(self.reset_cv_rune_defaults)

        # -----------------------------
        # LAYOUT
        # -----------------------------
        cv_layout = QVBoxLayout()

        # Top-right button layout
        cv_top_bar = QHBoxLayout()
        cv_top_bar.addStretch()
        cv_top_bar.addWidget(self.cv_return_button)

        # Mask previews
        player_preview_layout = QVBoxLayout()
        player_preview_layout.addWidget(self.player_mask_label)
        player_preview_layout.addWidget(self.player_contour_label)

        rune_preview_layout = QVBoxLayout()
        rune_preview_layout.addWidget(self.rune_mask_label)
        rune_preview_layout.addWidget(self.rune_contour_label)

        top_layout = QHBoxLayout()
        top_layout.addLayout(player_preview_layout, 4)
        top_layout.addLayout(rune_preview_layout, 4)

        player_slider_layout = QVBoxLayout()
        rune_slider_layout = QVBoxLayout()

        # ---- Player Mask Sliders ----
        player_slider_layout = QVBoxLayout()

        player_h_layout = QHBoxLayout()
        player_h_layout.addWidget(self.player_h_min_label)
        player_h_layout.addWidget(self.player_h_min)
        player_slider_layout.addLayout(player_h_layout)

        player_h_layout = QHBoxLayout()
        player_h_layout.addWidget(self.player_h_max_label)
        player_h_layout.addWidget(self.player_h_max)
        player_slider_layout.addLayout(player_h_layout)

        player_h_layout = QHBoxLayout()
        player_h_layout.addWidget(self.player_s_min_label)
        player_h_layout.addWidget(self.player_s_min)
        player_slider_layout.addLayout(player_h_layout)

        player_h_layout = QHBoxLayout()
        player_h_layout.addWidget(self.player_s_max_label)
        player_h_layout.addWidget(self.player_s_max)
        player_slider_layout.addLayout(player_h_layout)

        player_h_layout = QHBoxLayout()
        player_h_layout.addWidget(self.player_v_min_label)
        player_h_layout.addWidget(self.player_v_min)
        player_slider_layout.addLayout(player_h_layout)

        player_h_layout = QHBoxLayout()
        player_h_layout.addWidget(self.player_v_max_label)
        player_h_layout.addWidget(self.player_v_max)
        player_slider_layout.addLayout(player_h_layout)

        # ---- Rune Mask Sliders ----
        rune_slider_layout = QVBoxLayout()

        rune_h_layout = QHBoxLayout()
        rune_h_layout.addWidget(self.rune_h_min_label)
        rune_h_layout.addWidget(self.rune_h_min)
        rune_slider_layout.addLayout(rune_h_layout)

        rune_h_layout = QHBoxLayout()
        rune_h_layout.addWidget(self.rune_h_max_label)
        rune_h_layout.addWidget(self.rune_h_max)
        rune_slider_layout.addLayout(rune_h_layout)

        rune_h_layout = QHBoxLayout()
        rune_h_layout.addWidget(self.rune_s_min_label)
        rune_h_layout.addWidget(self.rune_s_min)
        rune_slider_layout.addLayout(rune_h_layout)

        rune_h_layout = QHBoxLayout()
        rune_h_layout.addWidget(self.rune_s_max_label)
        rune_h_layout.addWidget(self.rune_s_max)
        rune_slider_layout.addLayout(rune_h_layout)

        rune_h_layout = QHBoxLayout()
        rune_h_layout.addWidget(self.rune_v_min_label)
        rune_h_layout.addWidget(self.rune_v_min)
        rune_slider_layout.addLayout(rune_h_layout)

        rune_h_layout = QHBoxLayout()
        rune_h_layout.addWidget(self.rune_v_max_label)
        rune_h_layout.addWidget(self.rune_v_max)
        rune_slider_layout.addLayout(rune_h_layout)

        player_slider_layout.addWidget(self.cv_player_reset_button)
        rune_slider_layout.addWidget(self.cv_rune_reset_button)

        bottom_layout = QHBoxLayout()
        bottom_layout.addLayout(player_slider_layout)
        bottom_layout.addLayout(rune_slider_layout)

        # ---- CV Layout ----
        cv_layout = QVBoxLayout(self.cv_adjustment_widget)

        cv_layout.addLayout(cv_top_bar)
        cv_layout.addLayout(top_layout)
        cv_layout.addLayout(bottom_layout)

        self.setup_slider_constraints()

    # =========================================================
    # BUTTONS
    # =========================================================

    def enter_cv_adjustment(self):
        self.cv_adjustment_mode = True

        self.state.set_gui_stopped(True)
        self.normal_ui_widget.setVisible(False)
        self.cv_adjustment_widget.setVisible(True)

    def exit_cv_adjustment(self):
        self.cv_adjustment_mode = False

        self.state.set_gui_stopped(self.gui_paused)
        self.normal_ui_widget.setVisible(True)
        self.cv_adjustment_widget.setVisible(False)

    # =========================================================
    # SLIDERS
    # =========================================================

    def create_hsv_slider(self, name, minimum, maximum, value):
        label = QLabel(f"{name}: {value}")

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        slider.setValue(value)

        slider.valueChanged.connect(
            lambda value: label.setText(f"{name}: {value}")
        )

        return label, slider

    def setup_slider_constraints(self):
        # Player
        self.player_h_min.valueChanged.connect(
            lambda value: self.player_h_max.setMinimum(value)
        )
        self.player_h_max.valueChanged.connect(
            lambda value: self.player_h_min.setMaximum(value)
        )

        self.player_s_min.valueChanged.connect(
            lambda value: self.player_s_max.setMinimum(value)
        )
        self.player_s_max.valueChanged.connect(
            lambda value: self.player_s_min.setMaximum(value)
        )

        self.player_v_min.valueChanged.connect(
            lambda value: self.player_v_max.setMinimum(value)
        )
        self.player_v_max.valueChanged.connect(
            lambda value: self.player_v_min.setMaximum(value)
        )

        # Rune
        self.rune_h_min.valueChanged.connect(
            lambda value: self.rune_h_max.setMinimum(value)
        )
        self.rune_h_max.valueChanged.connect(
            lambda value: self.rune_h_min.setMaximum(value)
        )

        self.rune_s_min.valueChanged.connect(
            lambda value: self.rune_s_max.setMinimum(value)
        )
        self.rune_s_max.valueChanged.connect(
            lambda value: self.rune_s_min.setMaximum(value)
        )

        self.rune_v_min.valueChanged.connect(
            lambda value: self.rune_v_max.setMinimum(value)
        )
        self.rune_v_max.valueChanged.connect(
            lambda value: self.rune_v_min.setMaximum(value)
        )

    # =========================================================
    # MASKS
    # =========================================================

    def set_mask_image(self, label, mask):
        if mask is None:
            return

        h, w = mask.shape

        qt_img = QImage(
            mask.data,
            w,
            h,
            w,
            QImage.Format.Format_Grayscale8
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
    # CV UI UPDATE
    # =========================================================

    def update_cv_ui(self):
        player_mask = self.frame_state.get_player_mask()
        rune_mask = self.frame_state.get_rune_mask()

        self.set_mask_image(self.player_mask_label, player_mask)
        self.set_mask_image(self.rune_mask_label, rune_mask)

        player_size = self.frame_state.get_player_contour_size()
        rune_size = self.frame_state.get_rune_contour_size()

        self.player_contour_label.setText(
            f"Player Contour: {player_size}"
        )

        self.rune_contour_label.setText(
            f"Rune Contour: {rune_size}"
        )

    def update_player_hsv(self):
        lower = [
            self.player_h_min.value(),
            self.player_s_min.value(),
            self.player_v_min.value()
        ]

        upper = [
            self.player_h_max.value(),
            self.player_s_max.value(),
            self.player_v_max.value()
        ]

        self.vision_worker.set_player_hsv(lower, upper)

    def update_rune_hsv(self):
        lower = [
            self.rune_h_min.value(),
            self.rune_s_min.value(),
            self.rune_v_min.value()
        ]

        upper = [
            self.rune_h_max.value(),
            self.rune_s_max.value(),
            self.rune_v_max.value()
        ]

        self.vision_worker.set_rune_hsv(lower, upper)

    def reset_cv_player_defaults(self):
        self.vision_worker.reset_player_hsv()

    def reset_cv_rune_defaults(self):
        self.vision_worker.reset_rune_hsv()




