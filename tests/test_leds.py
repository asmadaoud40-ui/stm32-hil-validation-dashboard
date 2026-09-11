import pytest
@pytest.mark.parametrize(
	"command,expected",
	[
		("red on\r\n","LED RED ON"),
		("red off\r\n","LED RED OFF"),
		("green on\r\n","LED GREEN ON"),
		("green off\r\n","LED GREEN OFF"),
		("all on\r\n","LED GREEN ON\nLED RED ON"),
		("all off\r\n","LED GREEN OFF\nLED RED OFF"),
	]
)
def test_led_command(dut_serial, command, expected):

    dut_serial.reset_input_buffer()

    dut_serial.write(command.encode())
    dut_serial.flush()

    response = dut_serial.read(64)

    actual = response.decode()

    assert actual == expected