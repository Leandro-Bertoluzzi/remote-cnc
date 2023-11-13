import serial
import serial.tools.list_ports as serial_ports

class SerialService:
    def __init__(self):
        self.interface = serial.Serial()

    @classmethod
    def get_ports(cls):
        return serial_ports.comports()

    def startConnection(self, port: str, baudrate: int, timeout: int = 5) -> str:
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

        # Wait for the response
        return self.readLineUntilMessage()

    def sendLine(self, code: str):
        """Sends a line via serial port.
        """
        # Strip all EOL characters for consistency
        message = code.strip() + '\n'
        # Send line
        self.interface.write(message.encode('utf-8'))

    def streamLine(self, code: str) -> str:
        """Sends a line via serial port and waits for the response.
        """
        # Strip all EOL characters for consistency
        message = code.strip() + '\n'
        # Send line
        self.interface.write(message.encode('utf-8'))
        # Wait for the response
        return self.readLineUntilMessage()

    def readLine(self) -> str:
        """Waits for response with carriage return.
        """
        return self.interface.readline().decode('utf-8').strip()

    def readLineUntilMessage(self) -> str:
        """Waits for response with carriage return.
        Ignores empty messages and timeouts until an actual message arrives.
        """
        response = ''
        while not response:
            response = self.interface.readline().decode('utf-8').strip()
        return response

    def streamBlock(self, code: str) -> str:
        """Sends a block of code (multiple lines) via serial port.
        """
        # TODO: Pre-process and discard comment lines
        # Stream G-code to GRBL
        for line in code.splitlines():
            self.streamLine(line)
        return "OK"

    def stopConnection(self):
        """Closes any previous connection.
        """
        if self.interface.is_open:
            self.interface.close()
        return
