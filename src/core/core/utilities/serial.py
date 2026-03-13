import serial
import serial.tools.list_ports as serial_ports


class SerialService:
    def __init__(self):
        self.interface = serial.Serial()

    @classmethod
    def get_ports(cls):
        return serial_ports.comports()

    def startConnection(self, port: str, baudrate: int, timeout: int = 2) -> str:
        """Closes any previous connection and starts a new one.
        """
        # Close any previous serial connection
        if self.interface.is_open:
            self.interface.close()

        # Configure the new values
        self.interface.port = port
        self.interface.baudrate = baudrate
        self.interface.timeout = timeout

        # Start the connection
        self.interface.open()

        # Dump any data already received
        # self.interface.reset_input_buffer()

        # Wait for the response
        return self.readLineUntilMessage()

    def waiting(self) -> bool:
        return self.interface.in_waiting

    def sendBytes(self, code: bytes):
        """Sends byte(s) via serial port.
        """
        self.interface.write(code)

    def sendLine(self, code: str):
        """Sends a line via serial port.
        """
        # Strip all EOL characters for consistency
        message = code.strip() + '\n'
        # Send line
        self.interface.write(message.encode())

    def readLine(self) -> str:
        """Waits for response with carriage return.
        """
        return str(self.interface.readline().decode('ascii', 'ignore')).strip()

    def readLineUntilMessage(self, max_retries: int = 30) -> str:
        """Waits for response with carriage return.
        Ignores empty messages and timeouts until an actual message arrives.
        """
        response = ''
        retries = 0
        while not response and retries <= max_retries:
            response = self.readLine().strip()
            retries = retries + 1
        return response

    def stopConnection(self):
        """Closes any previous connection.
        """
        if self.interface.is_open:
            self.interface.close()
        return
