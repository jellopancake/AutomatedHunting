import time
from datetime import datetime
from zoneinfo import ZoneInfo
import math


class MovementController:
    def __init__(self, serial, state, config):
        self.serial = serial
        self.state = state
        self.config = config

    # -------------------------
    # Movement logic
    # -------------------------
    def move_to_start(self, rotation_step):
        start = rotation_step.get("startingLocation", {})

        goal_x = start.get("x", 20)
        goal_y = start.get("y", 20)
        tolerance = start.get("x tolerance", 2)
        align = start.get("align direction", "no")

        self.state.set_goal_position(goal_x, goal_y)

        print(f"[GOAL] x={goal_x}, y={goal_y}, tolerance={tolerance}, align={align}")

        if goal_x == -1 or goal_y == -1:
            return

        self._wait_until_stop()
        self._move_to_ground(goal_y, goal_x)
        self._walk_to_x(goal_x, tolerance, align)
        self._move_vertical(goal_y)

    def _wait_until_stop(self):
        time.sleep(1)
        while self.state.is_moving():
            time.sleep(0.1)

    # -------------------------
    # Horizontal movement
    # -------------------------
    def _walk_to_x(self, goal_x, tolerance, align):
        setup = self.config.get_setup_info()
        move_type = setup.get("horizontalMovement")
        move_dist = setup.get("horizontalMovementDistance")

        while True:
            if self._should_abort():
                self.reset_servos()
                return

            player_x, player_y = self.state.get_player_position()
            diff = abs(goal_x - player_x)

            print(f"[Player X] {player_x}, [Goal X] {goal_x}, [Difference] {diff}")

            if diff <= tolerance:
                self.reset_servos()
                self._align(goal_x, align)
                return

            direction = "Right" if goal_x > player_x else "Left"

            if diff >= move_dist and move_type in ("Flashjump", "Teleport"):
                self._fast_move(direction, diff, move_dist, move_type)

            elif diff >= 25 and move_type == "Glide":
                self._glide_move(direction, diff)

            elif diff >= 5:
                hold = self._calc_hold(diff, setup.get("walkMultiplier"), 0.82)
                self.walk(hold, direction)

            else:
                self.walk_short_distance(direction)
            
            if move_type == "Teleport":
                self.attack()
            self._wait()
            self._wait_until_stop()

    def _fast_move(self, direction, diff, dist, move_type):
        repeats = math.floor(diff / dist)
        print(f"[Repeats] {repeats}, [Move Distance] {dist}, [Difference] {diff}")

        self.start_walk(direction)

        for _ in range(repeats):
            if move_type == "Flashjump":
                self.double_jump_attack(direction)
            else:
                self.teleport()

        self.end_walk(direction)

    def _glide_move(self, direction, diff):
        hold = self._calc_hold(diff, 0.032, 0.6)
        while hold > 0:
            t = min(hold, 1.8)
            self.glide(t, direction)
            hold -= t
        

    def _align(self, goal_x, align):
        if align != "yes":
            return
        
        map_data = self.config.get_map_data()
        bounds = map_data.get("mapBounds", {})
        mw, mh = int(bounds.get("w", 0)), int(bounds.get("h", 0))

        midpoint = mw // 2

        if goal_x >= midpoint:
            self.walk_short_distance("Left")
        else:
            self.walk_short_distance("Right")

    # -------------------------
    # Vertical movement
    # -------------------------
    def _move_to_ground(self, goal_y, goal_x):
        setup = self.config.get_setup_info()
        move_type = setup.get("horizontalMovement")

        while True:
            if self._should_abort():
                self.reset_servos()
                return

            px, py = self.state.get_player_position()
            y_diff = goal_y - py
            x_diff = abs(goal_x - px)

            if abs(y_diff) <= 1:
                self.reset_servos()
                return

            elif y_diff >= 10:
                self.down_jump()

            else:
                return

            self.attack()
                
            self._wait()
            self._wait_until_stop()

    def _move_vertical(self, goal_y):
        setup = self.config.get_setup_info()
        move_type = setup.get("verticalMovement")

        while True:
            if self._should_abort():
                self.reset_servos()
                return

            px, py = self.state.get_player_position()
            diff = goal_y - py

            if abs(diff) <= 1:
                self.reset_servos()
                return

            elif diff >= 10:
                self.down_jump()

            elif diff >= -9 and diff <= -2:
                self.move_up()

            elif diff <= 9 and diff >= 2:
                self.move_down()

            elif diff <= -10 and diff >= -20:
                if move_type == "Teleport":
                    self.up_teleport()
                elif move_type == "Warrior Upjump":
                    if diff >= -14:
                        self.up_jump_warrior()
                    else:
                        self.rope_lift()
                elif move_type == "Glide":
                    self.rope_lift()
                else:
                    self.up_jump()
            
            elif diff <= -21:
                self.rope_lift()

            self.attack()

            self._wait()
            self._wait_until_stop()



    # -------------------------
    # Helpers
    # -------------------------
    def _calc_hold(self, diff, mult, offset):
        return max(0, (diff - offset) * mult)

    def _should_abort(self):
        return self.state.is_stopped() or self.state.is_gui_stopped()

    # -------------------------
    # Core helpers
    # -------------------------
    def _dir_to_param(self, direction: str) -> str:
        if direction == "Left":
            return '0'
        elif direction == "Right":
            return '1'
        else:
            raise ValueError("Invalid direction")

    def _send(self, command, param, delay):
        self.serial.submit(command, param, delay)

    # -------------------------
    # Basic actions
    # -------------------------
    def reset_servos(self):
        self._send("Reset Servos", '0', 500)

    def attack(self):
        self._send("Use Skill", '5', 500)

    def jump(self):
        self._send("Jump Skill", '5', 1400)

    def up_jump(self):
        self._send("Up Jump", '0', 1500)

    def down_jump(self):
        time.sleep(0.2)
        self._send("Down Jump", '0', 1500)

    def up_jump_warrior(self):
        self._send("Up Jump Warrior", '0', 1500)

    def teleport(self):
        self._send("Use Skill", '2', 500)

    def up_teleport(self):
        self._send("Up Teleport", '0', 1000)

    def rope_lift(self):
        self._send("Use Skill", '0', 1400)

    # -------------------------
    # Movement
    # -------------------------
    def start_walk(self, direction):
        self._send("Start Walk", self._dir_to_param(direction), 0)

    def end_walk(self, direction):
        self._send("End Walk", self._dir_to_param(direction), 0)

    def walk(self, hold_time, direction):
        self.start_walk(direction)
        time.sleep(hold_time)
        self.end_walk(direction)

    def walk_short_distance(self, direction):
        self._send("Walk Short Distance", self._dir_to_param(direction), 0)

    # -------------------------
    # Combat / skills
    # -------------------------
    def double_jump_attack(self, direction):
        self._send("Double Jump Attack", self._dir_to_param(direction), 1500)

    def end_hold_attack(self, param):
        self._send("End Hold Attack", param, 0)

    def move_down(self):
        self._send("Start Hold Attack", '7', 0)
        time.sleep(1)
        self._send("End Hold Attack", '7', 0)

    def move_up(self):
        self._send("Start Hold Attack", '6', 0)
        time.sleep(1)
        self._send("End Hold Attack", '6', 0)

    # -------------------------
    # Glide
    # -------------------------
    def start_glide(self, direction):
        self._send("Start Hold Glide", self._dir_to_param(direction), 200)

    def end_glide(self, direction):
        self._send("End Hold Glide", self._dir_to_param(direction), 0)

    def glide(self, hold_time, direction):
        self.start_glide(direction)
        time.sleep(hold_time)
        self.end_glide(direction)
        time.sleep(0.35)

    # =========================
    # Timing (non-blocking safe)
    # =========================
    def _wait(self, timeout = 30):
        start = time.time()

        while (time.time() - start) < timeout:
            if self.state.is_stopped() or self.state.is_gui_stopped() or self.state.is_queue_empty():
                return
            time.sleep(0.01)

    # -------------------------
    # Event
    # -------------------------
    def alien_swap(self):
        self._send("Swap Character", '0', 0)
        now_est = datetime.now(ZoneInfo("America/Toronto"))
        print(now_est)