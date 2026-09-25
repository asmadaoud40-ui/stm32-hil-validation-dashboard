import time
import serial


def open_serial_with_retry(port, baudrate, retries=5, delay=2):
    for attempt in range(retries):
        try:
            ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=2,
                write_timeout=2
            )

            time.sleep(1)
            return ser

        except serial.SerialException:
            if attempt == retries - 1:
                raise

            time.sleep(delay)