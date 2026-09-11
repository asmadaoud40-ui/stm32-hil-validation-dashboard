import time

def test_incomplete_command(dut_serial):

    dut_serial.reset_input_buffer()

    # Envoi d'une commande sans '\n'
    dut_serial.write(b"red on\r")
    dut_serial.flush()

    # Le firmware doit attendre la fin de trame
    response = dut_serial.read(64)

    assert response == b""

    # Cleanup du DUT :
    # on termine la trame restée en attente
    dut_serial.write(b"\n")
    dut_serial.flush()

    # On lit et on jette la réponse produite
    dut_serial.read(64)

def test_fragmented_command(dut_serial):

    dut_serial.reset_input_buffer()

    # Premier fragment
    dut_serial.write(b"green ")
    dut_serial.flush()

    # Délai volontaire entre les fragments
    time.sleep(0.5)

    # Deuxième fragment + fin de trame
    dut_serial.write(b"on\r\n")
    dut_serial.flush()

    response = dut_serial.read(64)

    actual = response.decode()
    expected = "LED GREEN ON"

    assert actual == expected


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