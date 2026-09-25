from tools.serial_connection import open_serial_with_retry
import pytest


@pytest.fixture(scope="session")
def dut_serial():
    ser = open_serial_with_retry("COM5", 9600)

    yield ser

    ser.close()


@pytest.fixture(scope="session")
def hil_serial():
    ser = open_serial_with_retry("COM7", 115200)

    yield ser

    ser.close()