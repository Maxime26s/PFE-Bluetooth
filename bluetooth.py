from machine import UART, Pin
import select
import time

max_chunk_size = 20
message_delimiter = "|"


class bluetooth:
    def __init__(self, uart: UART, timeout: int = 100) -> None:
        self.uart = uart
        self.at_mode = False
        self.poll = select.poll()
        self.poll.register(uart, select.POLLIN)
        self.timeout = timeout
        self.is_connected = False

    def has_unread_data(self) -> bool:
        return self.poll.poll(self.timeout) != []

    def read_app(self) -> bytes:
        received_message_buffer = bytearray()
        while self.has_unread_data():
            chunk = self.uart.read()
            print(chunk)
            if chunk.endswith(message_delimiter.encode()):
                received_message_buffer.extend(
                    chunk.rstrip(message_delimiter.encode()))
                response = bytes(received_message_buffer)
                received_message_buffer[:] = bytearray()
                print(f"READ: {response}")
                return response
            else:
                received_message_buffer.extend(chunk)
        return bytes()

    def read(self) -> bytes:
        response = self.uart.read()

        while self.has_unread_data():
            response += self.uart.read()

        print(f"READ: {response}")
        return response

    def read_at(self) -> bytes:
        response = bytes()

        while self.has_unread_data():
            response += self.uart.read()

        print(f"READ: {response}")
        return response

    def write(self, message) -> None:
        self.uart.write(message)
        print(f"WRITE: {message}")

    def write_long(self, message):
        chunks = [message[i:i + max_chunk_size]
                  for i in range(0, len(message), max_chunk_size)]
        for index, chunk in enumerate(chunks):
            chunk_with_delimiter = chunk + \
                message_delimiter if index == len(chunks) - 1 else chunk
            self.write(chunk_with_delimiter)
            time.sleep_ms(50)

    def send_at(self, cmd: str = "") -> bytes:
        if cmd != "":
            # if not self.at_mode:
            # self.start_at()
            command = f"AT+{cmd}"
        else:
            self.at_mode = True
            command = "AT"

        self.write(command)

        return self.read_at()

    def get_mac(self) -> bytes:
        return self.send_at("ADDR?")

    def get_name(self) -> bytes:
        return self.send_at("NAME?")

    def set_name(self, name: str) -> bytes:
        return self.send_at(f"NAME{name[:12]}")

    def disconnect(self) -> bytes:
        return self.send_at()

    def reset(self) -> bytes:
        return self.send_at("RESET")

    def set_notification(self, is_enabled: bool) -> bytes:
        if is_enabled:
            return self.send_at("NOTI1")
        else:
            return self.send_at("NOTI0")

    def set_baud(self, rate: int) -> bytes:
        if rate < 0 or rate > 8:
            return bytes("ERROR: Baud value must be between 0 and 8 (inclusive)")

        return self.send_at(f"BAUD{rate}")

    def start_at(self) -> bytes:
        response = self.disconnect()
        self.at_mode = True
        self.is_connected = False
        return response

    def stop_at(self) -> bytes:
        response = self.reset()
        self.at_mode = False
        return response

    def setup(self) -> None:
        self.start_at()
        self.set_notification(True)

        if "PICO" not in self.get_name():
            self.set_name("PICO-Test")

        self.stop_at()

    def try_read(self, app_mode: bool) -> bytes:
        if not self.at_mode and self.uart.any():
            if app_mode:
                return self.read_app()
            else:
                return self.read()
        return bytes()


if __name__ == "__main__":
    uart = UART(0, 115200)
    uart.init(0, 115200, rx=Pin(17), tx=Pin(16))
    bt = bluetooth(uart)
    bt.start_at()
    bt.set_baud(0)
    bt.stop_at()
