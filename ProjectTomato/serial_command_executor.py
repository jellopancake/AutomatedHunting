import serial
import threading
import time
import queue
import constants

class SerialCommandExecutor:
    def __init__(self, port, baudrate, state, bus):
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        time.sleep(2)

        self.bus = bus
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.state = state

        self._running = True
        self._shutdown_requested = False
        self._last_gen = self.state.get_generation()
        self._last_reset_gen = None

        self.bus.subscribe(
            "calibrate_key",
            self.handle_key_calibration,
            )

        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    # =========================
    # Public API (NON-BLOCKING)
    # =========================
    def submit(self, command_text, param='0', wait=0):
        gen = self.state.get_generation()
        item = (gen, command_text, param, wait)

        with self.lock:
            if command_text == "Reset Servos":
                # if same generation as last reset → ignore
                if self._last_reset_gen == gen:
                    return
                
                self._last_reset_gen = gen
            
            self.queue.put(item)

        self.check_queue()

        #with self.lock:
            #print([item for item in self.queue.queue if item[0] == self.state.get_generation()])
        

    def submit_config(self, double_jump_delay: str, short_double_jump_delay: str):
        self.queue.put((self.state.get_generation(), "CONFIG_SETUP", double_jump_delay, short_double_jump_delay))

    def stop(self):
        self._running = False

        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=2)

        if self.ser.is_open:
            self.ser.close()

    # =========================
    # Worker Loop
    # =========================
    def _run(self):
        while self._running:
            try:
                gen, cmd, param, wait = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
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
    def _execute(self, command_text, param1, param2):
        # =========================
        # CONFIG PACKET (CMD TYPE, PARAM 1, PARAM 2)
        # =========================
        if command_text == "CONFIG_SETUP":
            if len(param1) != 1 or len(param2) != 1:
                raise ValueError("CONFIG_SETUP requires 2 single-digit chars (param, wait_ms)")

            self._handshake()

            self.send_packet('*', param1, param2)

            print(f"[Serial CONFIG] * {param1}{param2}")

            return

        # =========================
        # CALIBRATION PACKET (CMD TYPE, PARAM1, PARAM2)
        # =========================

        if command_text == "CALIBRATION":
            key_number = int(param1)
            encoded_amount = int(param2)

            if not 0 <= key_number < 15:
                raise ValueError(f"Invalid key number: {key_number}")

            if not 0 <= encoded_amount <= 9:
                raise ValueError(f"Invalid adjustment: {encoded_amount}")

            if key_number >= 10:
                calibration_key = '>'
                calibration_param = str(key_number - 10)
            else:
                calibration_key = '<'
                calibration_param = str(key_number)

            self._handshake()

            self.send_packet(
                calibration_key,
                calibration_param,
                str(encoded_amount)
            )

            print(
                f"[Serial CALIBRATION] key={key_number}, "
                f"adjustment_code={encoded_amount}"
            )
            return

        # =========================
        # NORMAL COMMAND PACKET (CMD TYPE, CMD CHAR, WAIT MS)
        # =========================
        # param2 is wait_ms

        cmd_char = self.encode(command_text)

        if len(cmd_char) != 1 or len(param1) != 1:
            raise ValueError("Commands and params must be single characters")

        self._handshake()

        self.send_packet('+', cmd_char, param1)

        self.printToGUI(cmd_char, param1, param2)
        self._smart_delay(param2)

    def send_packet(self, param1, param2, param3):
        packet = bytes([
            ord(param1),
            ord(param2),
            ord(param3)
        ])

        with self.lock:
            self.ser.write(packet)

    # =========================
    # Handshake Protocol
    # =========================
    def _handshake(self):
        # send SYN
        self.ser.write(b"SYN\n")
        self._wait_line("SYN-ACK")

        self.ser.write(b"ACK\n")
        self._wait_line("READY")


    def _wait_line(self, expected, timeout=2.0):
        start = time.time()

        while time.time() - start < timeout:
            line = self.ser.readline().decode(errors="ignore").strip()

            if not line:
                continue

            if line == expected:
                return

            print("[Serial Unexpected]", line)
        
        print(f"[Serial Timeout Waiting For] {expected}")
        return False

    # -----------------------------
    # INTERRUPT BOOL
    # -----------------------------
    def _should_interrupt(self):
        return (
            self.state.is_stopped()
            or self.state.is_gui_stopped()
        )

    # =========================
    # Timing (non-blocking safe)
    # =========================
    def _smart_delay(self, wait_ms):
        start = time.time()

        while (time.time() - start) * 1000 < wait_ms:
            if self._should_interrupt():
                return
            time.sleep(0.01)

        if not self._should_interrupt():
            self.check_queue()

    def check_queue(self):
        gen = self.state.get_generation()
        remaining_queue = any(
            item[0] == gen and item[1] != "Reset Servos"
            for item in self.queue.queue
        )
        self.state.set_queue_empty(not remaining_queue)

    # =========================
    # Encode
    # =========================

    def encode(self, command_text):
        if command_text not in constants.serial_key:
            raise ValueError(f"Unknown command: {command_text}")
        return constants.serial_key[command_text]

    # =========================
    # Print to GUI
    # =========================    

    def printToGUI(self, cmd_char, param, wait_ms):
        cmd_name = constants.inverse_serial_key.get(cmd_char, "UNKNOWN")
        readable_param = self.parseAndReturnReadableParam(cmd_name, param)

        if readable_param == "no param":
            message = f"[Serial CMD] {cmd_name}, wait={wait_ms}ms"
        else:
            message = f"[Serial CMD] {cmd_name}, param={readable_param}, wait={wait_ms}ms"

        print(message)
        self.bus.emit("gui_message", message)

    def parseAndReturnReadableParam(self, cmd_name, param):
        cmd_type = constants.serial_key_data_type.get(cmd_name)

        if (cmd_type == "dir"):
            if param == '0':
                return "left"
            elif param == '1':
                return "right"
            else:
                return "incorrect param type(direction)"
        elif (cmd_type == "skill"):
            match param:
                case '0':
                    return "G"
                case '1':
                    return "CTRL"
                case '2':
                    return "H"
                case '3':
                    return "J"
                case '4':
                    return "ALT"
                case '5':
                    return "F"
                case '6':
                    return "UP"
                case '7':
                    return "DOWN"
                case '8':
                    return "APOS"
                case _:
                    return "incorrect param type(skill)"
        else:
            return "no param"

    # =========================
    # Calibration Event
    # =========================    

    def handle_key_calibration(self, data):
        key = data["key"]
        amount = data["amount"]

        key_number = constants.KEYS.index(key)

        # Map -5..-1 and +1..+5 to 0..9.
        encoded_amount = amount + 5
        if amount > 0:
            encoded_amount -= 1

        # Use the existing queue and worker thread.
        self.submit(
            "CALIBRATION",
            str(key_number),
            str(encoded_amount)
        )


    