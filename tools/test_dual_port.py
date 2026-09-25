from tools.serial_connection import open_serial_with_retry


# ==========================================
# 1. Open the same ports as pytest fixtures
# ==========================================

dut_serial = open_serial_with_retry("COM5", 9600)
hil_serial = open_serial_with_retry("COM7", 115200)

print("COM5 ouvert :", dut_serial.is_open)
print("COM7 ouvert :", hil_serial.is_open)


# ==========================================
# 2. Same buffer reset as pytest
# ==========================================

dut_serial.reset_input_buffer()
hil_serial.reset_input_buffer()


# ==========================================
# 3. Same SETUP command as pytest
# ==========================================

setup_cmd = b"all off\r\n"

print("Envoi setup :", setup_cmd)

dut_serial.write(setup_cmd)
dut_serial.flush()

setup_response = dut_serial.read(64)

print("Réponse setup brute :", repr(setup_response))


# ==========================================
# 4. Same tested command as pytest
# ==========================================

command = b"red on\r\n"

print("Envoi commande :", command)

dut_serial.write(command)
dut_serial.flush()

response = dut_serial.read(64)

print("Réponse STM32 brute :", repr(response))
print("Réponse STM32 texte :", response.decode(errors="replace"))


# ==========================================
# 5. Same Arduino HIL verification
# ==========================================

hil_serial.write(b"READ\n")
hil_serial.flush()

gpio_state = hil_serial.readline().decode().strip()

print("Réponse HIL :", gpio_state)


# ==========================================
# 6. Close
# ==========================================

dut_serial.close()
hil_serial.close()

print("Ports fermés")