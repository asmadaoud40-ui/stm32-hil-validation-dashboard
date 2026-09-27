import pytest


@pytest.mark.parametrize(
    "command, expected_lines",
    [
        ("red on\r\n", ["LED RED ON"]),
        ("red off\r\n", ["LED RED OFF"]),
        ("green on\r\n", ["LED GREEN ON"]),
        ("green off\r\n", ["LED GREEN OFF"]),
        ("all on\r\n", ["LED GREEN ON", "LED RED ON"]),
        ("all off\r\n", ["LED GREEN OFF", "LED RED OFF"]),
    ]
)
def test_led_command(dut_serial, command, expected_lines):

    dut_serial.reset_input_buffer()

    dut_serial.write(command.encode())
    dut_serial.flush()

    actual_lines = []

    for _ in expected_lines:
        line = dut_serial.readline().decode().strip()
        actual_lines.append(line)

    assert actual_lines == expected_lines