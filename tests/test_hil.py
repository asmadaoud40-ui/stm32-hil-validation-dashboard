import pytest


@pytest.mark.parametrize(
    "setup_cmd, command, expected_uart, expected_gpio",
    [
        (b"all off\r\n",   b"red on\r\n",
         "LED RED ON", "GREEN=0,RED=1"),

        (b"red on\r\n",    b"red off\r\n",
         "LED RED OFF", "GREEN=0,RED=0"),

        (b"all off\r\n",   b"green on\r\n",
         "LED GREEN ON", "GREEN=1,RED=0"),

        (b"green on\r\n",  b"green off\r\n",
         "LED GREEN OFF", "GREEN=0,RED=0"),

        (b"all off\r\n",   b"all on\r\n",
         "LED GREEN ON\nLED RED ON", "GREEN=1,RED=1"),

        (b"all on\r\n",    b"all off\r\n",
         "LED GREEN OFF\nLED RED OFF", "GREEN=0,RED=0"),
    ]
)
def test_hil_led_commands(
        dut_serial,
        hil_serial,
        setup_cmd,
        command,
        expected_uart,
        expected_gpio):

    dut_serial.reset_input_buffer()
    hil_serial.reset_input_buffer()

    # Mettre le hardware dans l'état opposé/initial connu
    dut_serial.write(setup_cmd)
    dut_serial.flush()
    dut_serial.read(64)

    # Envoyer la vraie commande testée
    dut_serial.write(command)
    dut_serial.flush()

    # Vérification software
    response = dut_serial.read(64).decode()
    assert response == expected_uart

    # Vérification hardware indépendante
    hil_serial.write(b"READ\n")
    hil_serial.flush()

    gpio_state = hil_serial.readline().decode().strip()
    assert gpio_state == expected_gpio
