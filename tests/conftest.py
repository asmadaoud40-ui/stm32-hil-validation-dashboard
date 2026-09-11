import serial
import time
import pytest


@pytest.fixture(scope="session")
def dut_serial():

    ser = serial.Serial(
        port="COM5",
        baudrate=9600,
        timeout=2,
        write_timeout=2
    )

    time.sleep(1)

    yield ser

    ser.close()