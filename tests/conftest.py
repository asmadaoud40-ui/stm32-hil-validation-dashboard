import serial
import time
import pytest


@pytest.fixture(scope="session")
def dut_serial():

    # Créer l'objet série sans ouvrir immédiatement le port
    ser = serial.Serial()

    # Configuration de la liaison
    ser.port = "COM5"
    ser.baudrate = 9600
    ser.timeout = 2
    ser.write_timeout = 2

    # Essayer d'ouvrir COM5 jusqu'à 5 fois
    for attempt in range(1, 6):

        try:
            ser.open()
            print(f"COM5 opened on attempt {attempt}")
            break

        except serial.SerialException:

            print(f"COM5 unavailable - attempt {attempt}/5")

            # Si c'était la dernière tentative,
            # laisser l'erreur remonter vers pytest
            if attempt == 5:
                raise

            # Laisser Windows / Bluetooth libérer le port
            time.sleep(2)

    # Laisser la liaison Bluetooth se stabiliser
    time.sleep(1)

    try:
        # Fournir la connexion aux tests
        yield ser

    finally:
        # Teardown :
        # fermer COM5 même si un test FAIL
        if ser.is_open:
            ser.close()