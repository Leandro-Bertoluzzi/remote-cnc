import serial

class SerialService:
    def __init__(self):
        self.interface = serial.Serial()

    def startConnection(self, port: str, baudrate: int, timeout: int = 5):
        # Close any previous serial connection
        if self.interface.is_open:
            self.interface.close()

        # Configure the new values
        self.interface.port = port
        self.interface.baudrate = baudrate
        self.interface.timeout = timeout

        # Start the connection
        self.interface.open()

        # Wait for the Arduino to set up
        #time.sleep(2)
        startMessage = self.interface.readline().decode('utf-8').strip()
        # TODO: Add validation for the startup message

        return

    def streamLine(self, code: str):
        # Strip all EOL characters for consistency
        message = code.strip() + '\n'
        # Send G-code line to GRBL
        self.interface.write(message.encode('utf-8'))
        # Wait for GRBL response with carriage return
        grbl_out = self.interface.readline().strip()
        # TODO: Add validation for the response message

        return "OK"

    def streamBlock(self, code: str):
        # TODO: Pre-process and discard comment lines
        # Stream G-code to GRBL
        for line in code.splitlines():
            self.streamLine(line)
        return "OK"

    def stopConnection(self):
        # Close any previous serial connection
        if self.interface.is_open:
            self.interface.close()
        return
