import serial
import time

ser = serial.Serial(
    port="COM5",
    baudrate=9600,
    timeout=2,
    write_timeout=2
)

print("COM5 ouvert")

time.sleep(1)

ser.reset_input_buffer()

ser.write(b"red on\r\n")
ser.flush()

print("Commande envoyée")

response = ser.read(64)

print("Réponse brute :", repr(response))

if response:
    print("STM32 response :", response.decode())
else:
    print("Aucune réponse reçue")

ser.close()

print("COM5 fermé")