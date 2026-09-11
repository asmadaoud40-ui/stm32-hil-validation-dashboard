import time


def test_back_to_back_commands(dut_serial):

    dut_serial.reset_input_buffer()

    # Premier fragment
    dut_serial.write(b"red on\r\nred off\r\n")
    dut_serial.flush()

    # Lire la réponse du DUT
    response = dut_serial.read(64)

    actual = response.decode()
    expected = "LED RED ONLED RED OFF"

    assert actual == expected