import serial
import threading
import time
import queue
import constants

class SerialCommandExecutor:
    def __init__(self, port, baudrate, state):
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        time.sleep(2)

        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.state = state

        self._running = True
        self._last_gen = self.state.get_generation()

        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    # =========================
    # Public API (NON-BLOCKING)
    # =========================
    def submit(self, command_text, param='0', wait=0):
        #add an artifical delay
        #wait = wait + 100
        self.queue.put((self.state.get_generation(), command_text, param, wait))

    def submit_config(self, double_jump_delay, short_double_jump_delay):
        self.queue.put((self.state.get_generation(), "CONFIG_SETUP", double_jump_delay, short_double_jump_delay))

    def stop(self):
        self._running = False

    # =========================
    # Worker Loop
    # =========================
    def _run(self):
        while self._running:
            gen, cmd, param, wait = self.queue.get()
            current_gen = self.state.get_generation()

            if gen != current_gen:
                if self._last_gen != current_gen:
                    self._send_reset_servos()
                    self._last_gen = current_gen

                self.queue.task_done()
                continue

            self._execute(cmd, param, wait)
            self.queue.task_done()

    def _send_reset_servos(self):
        try:
            self._execute("Reset Servos", '0', 1000)
        except Exception as e:
            print("[Serial Reset Error]", e)

    # =========================
    # Core Execution
    # =========================
    def _execute(self, command_text, param, wait_ms):
        # =========================
        # CONFIG PACKET
        # =========================
        if command_text == "CONFIG_SETUP":
            if len(param) != 1 or len(wait_ms) != 1:
                raise ValueError("CONFIG_SETUP requires 2 single-digit chars (param, wait_ms)")

            packet = bytes([
                ord('*'),
                ord(param),
                ord(wait_ms)
            ])

            with self.lock:
                self.ser.write(packet)

            print(f"[Serial CONFIG] * {param}{wait_ms}")
            return

        # =========================
        # NORMAL COMMAND PACKET
        # =========================
        cmd_char = self.encode(command_text)

        if len(cmd_char) != 1 or len(param) != 1:
            raise ValueError("Commands and params must be single characters")

        self._handshake()

        packet = bytes([
            ord('+'),
            ord(cmd_char),
            ord(param)
        ])

        with self.lock:
            self.ser.write(packet)

        cmd_name = constants.inverse_serial_key.get(cmd_char, "UNKNOWN")
        print(f"[Serial CMD] + {cmd_name}, param={param}, wait={wait_ms}")

        self._smart_delay(wait_ms)

    # =========================
    # Handshake Protocol
    # =========================
    def _handshake(self):
        # send SYN
        self.ser.write(b"SYN\n")
        self._wait_line("SYN-ACK")

        self.ser.write(b"ACK\n")
        self._wait_line("READY")

    def _wait_line(self, expected):
        while True:
            line = self.ser.readline().decode().strip()
            if not line:
                continue

            if line == expected:
                return

            print("[Serial Unexpected]", line)

    # =========================
    # Timing (non-blocking safe)
    # =========================
    def _smart_delay(self, wait_ms):
        start = time.time()

        while (time.time() - start) * 1000 < wait_ms:
            if self.state.is_stopped():
                return
            time.sleep(0.01)

    # =========================
    # Encode
    # =========================

    def encode(self, command_text):
        if command_text not in constants.serial_key:
            raise ValueError(f"Unknown command: {command_text}")
        return constants.serial_key[command_text]