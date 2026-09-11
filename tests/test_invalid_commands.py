import pytest
@pytest.mark.parametrize(
	"command,expected",
	[
		("RED ON\r\n", "ERROR INVALID COMMAND"),      # mauvaise casse
		("blue on\r\n", "ERROR INVALID COMMAND"),     # commande inconnue
		("red start\r\n", "ERROR INVALID COMMAND"),   # argument invalide
		("red  on\r\n", "ERROR INVALID COMMAND"),     # double espace
		("@@@\r\n", "ERROR INVALID COMMAND"),         # caractères inattendus
		("\r\n", "ERROR INVALID COMMAND"),            # commande vide
	]
)
def test_invalid_command(dut_serial, command, expected):

    dut_serial.reset_input_buffer()

    dut_serial.write(command.encode())
    dut_serial.flush()

    response = dut_serial.read(64)

    actual = response.decode()

    assert actual == expected