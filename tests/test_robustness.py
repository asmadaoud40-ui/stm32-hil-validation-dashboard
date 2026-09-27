import time


def test_incomplete_command(dut_serial):

    dut_serial.reset_input_buffer()

    dut_serial.write(b"red on\r")
    dut_serial.flush()

    # Ici on vérifie volontairement qu'aucune réponse n'arrive
    response = dut_serial.read(64)

    assert response == b""

    # Terminer la commande
    dut_serial.write(b"\n")
    dut_serial.flush()

    # Nettoyer la réponse
    dut_serial.readline()


def test_fragmented_command(dut_serial):

    dut_serial.reset_input_buffer()

    dut_serial.write(b"green ")
    dut_serial.flush()

    time.sleep(0.5)

    dut_serial.write(b"on\r\n")
    dut_serial.flush()

    response = dut_serial.readline().decode().strip()

    assert response == "LED GREEN ON"


def test_back_to_back_commands(dut_serial):

    dut_serial.reset_input_buffer()

    dut_serial.write(b"red on\r\nred off\r\n")
    dut_serial.flush()

    response = dut_serial.read(64)

    actual = response.decode()
    expected = "LED RED ONLED RED OFF"

    assert actual == expected