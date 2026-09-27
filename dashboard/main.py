import sys
import time
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QPlainTextEdit,
    QLabel,
    QTableWidget,
    QTableWidgetItem
)

from tools.serial_connection import open_serial_with_retry


# ============================================================
# APPLICATION QT
# ============================================================

app = QApplication(sys.argv)

ui_path = Path(__file__).with_name("dashboard.ui")

ui_file = QFile(str(ui_path))
ui_file.open(QFile.ReadOnly)

loader = QUiLoader()
window = loader.load(ui_file)

ui_file.close()


# ============================================================
# WIDGETS
# ============================================================

red_on_button = window.findChild(QPushButton, "redonbutton")
red_off_button = window.findChild(QPushButton, "redoffbutton")

green_on_button = window.findChild(QPushButton, "greenonbutton")
green_off_button = window.findChild(QPushButton, "greenoffbutton")

all_on_button = window.findChild(QPushButton, "allonbutton")
all_off_button = window.findChild(QPushButton, "alloffbutton")

green_led_state_label = window.findChild(
    QLabel,
    "greenLedStateLabel"
)

red_led_state_label = window.findChild(
    QLabel,
    "redLedStateLabel"
)

run_uart_button = window.findChild(
    QPushButton,
    "runuartbutton"
)

run_hil_button = window.findChild(
    QPushButton,
    "runhilbutton"
)

generate_report_button = window.findChild(
    QPushButton,
    "generatereportbutton"
)

test_results_table = window.findChild(
    QTableWidget,
    "testResultsTable"
)

serial_console = window.findChild(
    QPlainTextEdit,
    "serialConsole"
)


# ============================================================
# SERIAL CONNECTIONS
# ============================================================

dut_serial = open_serial_with_retry(
    "COM5",
    9600
)

hil_serial = open_serial_with_retry(
    "COM7",
    115200
)

time.sleep(2)

dut_serial.reset_input_buffer()
hil_serial.reset_input_buffer()


# ============================================================
# HIL
# ============================================================

def read_hil_state():

    hil_serial.reset_input_buffer()

    hil_serial.write(b"READ\n")

    return hil_serial.readline().decode().strip()


# ============================================================
# HARDWARE MONITOR
# ============================================================

def update_hardware_monitor(hil_state):

    if "GREEN=1" in hil_state:
        green_led_state_label.setText("ON")
    else:
        green_led_state_label.setText("OFF")

    if "RED=1" in hil_state:
        red_led_state_label.setText("ON")
    else:
        red_led_state_label.setText("OFF")


# ============================================================
# DUT COMMAND
# ============================================================

def send_dut_command(command):

    serial_console.appendPlainText(
        f"[TX] {command}"
    )

    dut_serial.reset_input_buffer()

    dut_serial.write(
        (command + "\r\n").encode()
    )

    response = (
        dut_serial
        .readline()
        .decode()
        .strip()
    )

    serial_console.appendPlainText(
        f"[RX] {response}"
    )

    hil_state = read_hil_state()

    serial_console.appendPlainText(
        f"[HIL] {hil_state}"
    )

    update_hardware_monitor(
        hil_state
    )


# ============================================================
# UART TESTS
# ============================================================

def run_uart_tests():

    global dut_serial

    serial_console.appendPlainText(
        "[TEST] Running UART tests..."
    )

    # Libérer COM5 pour pytest
    dut_serial.close()

    project_root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",

            "tests/test_leds.py",
            "tests/test_invalid_commands.py",
            "tests/test_robustness.py",

            "-q",

            "--junitxml=reports/dashboard_uart.xml",
        ],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    serial_console.appendPlainText(
        result.stdout
    )

    load_test_results(
        project_root
        / "reports"
        / "dashboard_uart.xml",

        "UART"
    )

    # Reprendre COM5
    dut_serial = open_serial_with_retry(
        "COM5",
        9600
    )


# ============================================================
# HIL TESTS
# ============================================================

def run_hil_tests():

    global dut_serial, hil_serial

    serial_console.appendPlainText(
        "[TEST] Running HIL tests..."
    )

    # Libérer COM5 et COM7 pour pytest
    dut_serial.close()
    hil_serial.close()

    project_root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",

            "tests/test_hil.py",

            "-q",

            "--junitxml=reports/dashboard_hil.xml",
        ],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    serial_console.appendPlainText(
        result.stdout
    )

    load_test_results(
        project_root
        / "reports"
        / "dashboard_hil.xml",

        "HIL"
    )

    # Reprendre COM5
    dut_serial = open_serial_with_retry(
        "COM5",
        9600
    )

    # Reprendre COM7
    hil_serial = open_serial_with_retry(
        "COM7",
        115200
    )


# ============================================================
# GENERATE FULL REPORT
# ============================================================

def generate_report():

    global dut_serial, hil_serial

    serial_console.appendPlainText(
        "[REPORT] Running complete validation campaign..."
    )

    # --------------------------------------------------------
    # pytest doit utiliser COM5 et COM7
    # donc le dashboard doit les libérer
    # --------------------------------------------------------

    dut_serial.close()
    hil_serial.close()

    project_root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    reports_dir = project_root / "reports"

    # Crée le dossier reports s'il n'existe pas
    reports_dir.mkdir(
        exist_ok=True
    )

    # --------------------------------------------------------
    # Lancer TOUS les tests
    # +
    # générer HTML
    # +
    # générer JUnit XML
    # --------------------------------------------------------

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",

            "--html=reports/test_report.html",
            "--self-contained-html",

            "--junitxml=reports/results.xml",
        ],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    # --------------------------------------------------------
    # Afficher résultat pytest dans Serial Console
    # --------------------------------------------------------

    serial_console.appendPlainText(
        result.stdout
    )

    # En cas d'erreur Python / pytest
    if result.stderr:
        serial_console.appendPlainText(
            result.stderr
        )

    # --------------------------------------------------------
    # Afficher les 21 résultats dans Test Results
    # --------------------------------------------------------

    load_test_results(
        reports_dir / "results.xml",
        "FULL"
    )

    # --------------------------------------------------------
    # Vérifier résultat global
    # --------------------------------------------------------

    if result.returncode == 0:

        serial_console.appendPlainText(
            "[REPORT] Validation PASSED"
        )

        serial_console.appendPlainText(
            "[REPORT] HTML report generated:"
        )

        serial_console.appendPlainText(
            str(reports_dir / "test_report.html")
        )

        serial_console.appendPlainText(
            "[REPORT] JUnit XML generated:"
        )

        serial_console.appendPlainText(
            str(reports_dir / "results.xml")
        )

    else:

        serial_console.appendPlainText(
            "[REPORT] Validation FAILED"
        )

    # --------------------------------------------------------
    # Reprendre les ports après pytest
    # --------------------------------------------------------

    dut_serial = open_serial_with_retry(
        "COM5",
        9600
    )

    hil_serial = open_serial_with_retry(
        "COM7",
        115200
    )


# ============================================================
# XML -> TEST RESULTS TABLE
# ============================================================

def load_test_results(
    xml_path,
    test_type
):

    # Ouvrir le fichier XML
    tree = ET.parse(
        xml_path
    )

    root = tree.getroot()

    # Effacer ancien contenu du tableau
    test_results_table.setRowCount(0)

    # Parcourir chaque test pytest
    for testcase in root.iter("testcase"):

        test_name = testcase.get(
            "name"
        )

        duration = testcase.get(
            "time",
            "0"
        )

        # ----------------------------------------------------
        # Déterminer PASS / FAIL / ERROR / SKIPPED
        # ----------------------------------------------------

        if testcase.find("failure") is not None:

            status = "FAIL"

        elif testcase.find("error") is not None:

            status = "ERROR"

        elif testcase.find("skipped") is not None:

            status = "SKIPPED"

        else:

            status = "PASS"

        # ----------------------------------------------------
        # Ajouter ligne dans tableau
        # ----------------------------------------------------

        row = test_results_table.rowCount()

        test_results_table.insertRow(
            row
        )

        # Test Name
        test_results_table.setItem(
            row,
            0,
            QTableWidgetItem(
                test_name
            )
        )

        # Type
        test_results_table.setItem(
            row,
            1,
            QTableWidgetItem(
                test_type
            )
        )

        # Status
        test_results_table.setItem(
            row,
            2,
            QTableWidgetItem(
                status
            )
        )

        # Duration
        test_results_table.setItem(
            row,
            3,
            QTableWidgetItem(
                f"{float(duration):.2f} s"
            )
        )


# ============================================================
# BUTTON HANDLERS
# ============================================================

def handle_red_on():

    send_dut_command(
        "red on"
    )


def handle_red_off():

    send_dut_command(
        "red off"
    )


def handle_green_on():

    send_dut_command(
        "green on"
    )


def handle_green_off():

    send_dut_command(
        "green off"
    )


def handle_all_on():

    send_dut_command(
        "all on"
    )


def handle_all_off():

    send_dut_command(
        "all off"
    )


# ============================================================
# SIGNALS
# ============================================================

red_on_button.clicked.connect(
    handle_red_on
)

red_off_button.clicked.connect(
    handle_red_off
)

green_on_button.clicked.connect(
    handle_green_on
)

green_off_button.clicked.connect(
    handle_green_off
)

all_on_button.clicked.connect(
    handle_all_on
)

all_off_button.clicked.connect(
    handle_all_off
)

run_uart_button.clicked.connect(
    run_uart_tests
)

run_hil_button.clicked.connect(
    run_hil_tests
)

generate_report_button.clicked.connect(
    generate_report
)


# ============================================================
# START GUI
# ============================================================

window.show()

sys.exit(
    app.exec()
)