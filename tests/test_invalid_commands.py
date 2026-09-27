import pytest


@pytest.mark.parametrize(
    "command, expected",
    [
        ("RED ON\r\n", "ERROR INVALID COMMAND"),
        ("blue on\r\n", "ERROR INVALID COMMAND"),
        ("red start\r\n", "ERROR INVALID COMMAND"),
        ("red  on\r\n", "ERROR INVALID COMMAND"),
        ("@@@\r\n", "ERROR INVALID COMMAND"),
        ("\r\n", "ERROR INVALID COMMAND"),
    ]
)
def test_invalid_command(dut_serial, command, expected):

    dut_serial.reset_input_buffer()

    dut_serial.write(command.encode())
    dut_serial.flush()

    response = dut_serial.readline().decode().strip()

    assert response == expected