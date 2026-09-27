import pytest


def read_dut_response(dut_serial, command):

    if b"all on" in command or b"all off" in command:
        line_1 = dut_serial.readline().decode().strip()
        line_2 = dut_serial.readline().decode().strip()

        return line_1 + "\n" + line_2

    return dut_serial.readline().decode().strip()


@pytest.mark.parametrize(
    "setup_cmd, command, expected_uart, expected_gpio",
    [
        (
            b"all off\r\n",
            b"red on\r\n",
            "LED RED ON",
            "GREEN=0,RED=1"
        ),
        (
            b"red on\r\n",
            b"red off\r\n",
            "LED RED OFF",
            "GREEN=0,RED=0"
        ),
        (
            b"all off\r\n",
            b"green on\r\n",
            "LED GREEN ON",
            "GREEN=1,RED=0"
        ),
        (
            b"green on\r\n",
            b"green off\r\n",
            "LED GREEN OFF",
            "GREEN=0,RED=0"
        ),
        (
            b"all off\r\n",
            b"all on\r\n",
            "LED GREEN ON\nLED RED ON",
            "GREEN=1,RED=1"
        ),
        (
            b"all on\r\n",
            b"all off\r\n",
            "LED GREEN OFF\nLED RED OFF",
            "GREEN=0,RED=0"
        ),
    ]
)
def test_hil_led_commands(
    dut_serial,
    hil_serial,
    setup_cmd,
    command,
    expected_uart,
    expected_gpio
):

    dut_serial.reset_input_buffer()
    hil_serial.reset_input_buffer()

    # Mettre le DUT dans un état connu
    dut_serial.write(setup_cmd)
    dut_serial.flush()

    # IMPORTANT : vider toute la réponse du setup
    read_dut_response(dut_serial, setup_cmd)

    # Commande réellement testée
    dut_serial.write(command)
    dut_serial.flush()

    response = read_dut_response(dut_serial, command)

    assert response == expected_uart

    # Vérification physique par Arduino
    hil_serial.write(b"READ\n")
    hil_serial.flush()

    gpio_state = hil_serial.readline().decode().strip()

    assert gpio_state == expected_gpio