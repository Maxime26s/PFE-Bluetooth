from machine import Pin, UART
import time
import select


class bluetooth:
    def __init__(self, uart: UART, timeout: int = 100) -> None:
        self.uart = uart
        self.at_mode = False
        self.poll = select.poll()
        self.poll.register(uart, select.POLLIN)
        self.timeout = timeout
        self.is_connected = False
        self.setup()

    def has_unread_data(self) -> bool:
        return self.poll.poll(self.timeout) != []

    def read(self) -> bytearray:
        response = bytearray()

        while self.has_unread_data():
            response += self.uart.read()

        print(f"READ: {response}")
        return response

    def write(self, message) -> None:
        self.uart.write(message)
        print(f"WRITE: {message}")

    def send_at(self, cmd: str = "") -> bytearray:
        self.at_mode = True

        if cmd != "":
            command = f"AT+{cmd}"
        else:
            command = "AT"

        self.write(command)

        return self.read()

    def get_mac(self) -> bytearray:
        return self.send_at("ADDR?")

    def get_name(self) -> bytearray:
        return self.send_at("NAME?")

    def set_name(self, name: str) -> bytearray:
        return self.send_at(f"NAME{name[:12]}")

    def disconnect(self) -> bytearray:
        return self.send_at()

    def reset(self) -> bytearray:
        return self.send_at("RESET")

    def set_notification(self, is_enabled: bool) -> bytearray:
        if is_enabled:
            return self.send_at("NOTI1")
        else:
            return self.send_at("NOTI0")
        
    def set_baud(self, rate: int) -> bytearray:
        return self.send_at(f"BAUD{rate}")

    def start_at(self) -> bytearray:
        response = self.disconnect()
        self.at_mode = True
        self.is_connected = False
        return response

    def stop_at(self) -> bytearray:
        response = self.reset()
        self.at_mode = False
        return response

    def setup(self) -> None:
        self.start_at()
        self.set_baud(4)
        self.set_notification(True)

        if "PICO" not in self.get_name():
            self.set_name("PICO-Test")

        self.stop_at()

    def read_message(self) -> bytearray:
        if not self.at_mode and self.uart.any():
            return self.read()
        return bytearray()
