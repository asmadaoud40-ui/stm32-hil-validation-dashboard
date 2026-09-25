import sys
import time
from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QPushButton, QPlainTextEdit

from tools.serial_connection import open_serial_with_retry


app = QApplication(sys.argv)

ui_path = Path(__file__).with_name("dashboard.ui")
ui_file = QFile(str(ui_path))
ui_file.open(QFile.ReadOnly)

loader = QUiLoader()
window = loader.load(ui_file)

ui_file.close()


# ---------- Widgets ----------

red_on_button = window.findChild(QPushButton, "redonbutton")
red_off_button = window.findChild(QPushButton, "redoffbutton")
green_on_button = window.findChild(QPushButton, "greenonbutton")
green_off_button = window.findChild(QPushButton, "greenoffbutton")
all_on_button = window.findChild(QPushButton, "allonbutton")
all_off_button = window.findChild(QPushButton, "alloffbutton")

serial_console = window.findChild(QPlainTextEdit, "serialConsole")


# ---------- Serial connections ----------

dut_serial = open_serial_with_retry("COM5", 9600)

hil_serial = open_serial_with_retry("COM7", 115200)

time.sleep(2)

dut_serial.reset_input_buffer()
hil_serial.reset_input_buffer()


# ---------- HIL ----------

def read_hil_state():
    hil_serial.reset_input_buffer()

    hil_serial.write(b"READ\n")

    return hil_serial.readline().decode().strip()


# ---------- DUT ----------

def send_dut_command(command):
    serial_console.appendPlainText(f"[TX] {command}")

    dut_serial.reset_input_buffer()

    dut_serial.write((command + "\r\n").encode())

    response = dut_serial.readline().decode().strip()

    serial_console.appendPlainText(f"[RX] {response}")

    hil_state = read_hil_state()

    serial_console.appendPlainText(f"[HIL] {hil_state}")


# ---------- Button handlers ----------

def handle_red_on():
    send_dut_command("red on")


def handle_red_off():
    send_dut_command("red off")


def handle_green_on():
    send_dut_command("green on")


def handle_green_off():
    send_dut_command("green off")


def handle_all_on():
    send_dut_command("all on")


def handle_all_off():
    send_dut_command("all off")


# ---------- Signals ----------

red_on_button.clicked.connect(handle_red_on)
red_off_button.clicked.connect(handle_red_off)
green_on_button.clicked.connect(handle_green_on)
green_off_button.clicked.connect(handle_green_off)
all_on_button.clicked.connect(handle_all_on)
all_off_button.clicked.connect(handle_all_off)


# ---------- Start GUI ----------

window.show()

sys.exit(app.exec())