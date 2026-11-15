"""STM32 HIL Validation Dashboard.

The dashboard controls the STM32 DUT over Bluetooth COM5 / USART6, observes
GPIO states through the Arduino HIL monitor on COM7, runs pytest campaigns,
opens local reports, and displays the latest GitHub Actions workflow status.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QFile, QProcess, QThread, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


# -----------------------------------------------------------------------------
# Project paths and settings
# -----------------------------------------------------------------------------

DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DASHBOARD_DIR.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
CI_CONFIG_PATH = DASHBOARD_DIR / "ci_config.json"

DEFAULT_CI_CONFIG = {
    "repository": "asmadaoud40-ui/stm32-hil-validation-ci",
    "workflow_file": "hil-ci.yml",
    "branch": "main",
    "refresh_interval_seconds": 300,
}

APP_STYLE = r"""
QMainWindow, QWidget#centralwidget {
    background: #F4F6F8;
    color: #243244;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 9pt;
}
QFrame#headerFrame {
    background: #17324D;
    border: 1px solid #17324D;
    border-radius: 0px;
}
QLabel#titleLabel {
    color: #FFFFFF;
    font-size: 20pt;
    font-weight: 700;
}
QLabel#subtitleLabel { color: #D2DCE7; font-size: 8.5pt; }
QFrame#dutCard, QFrame#hilCard, QFrame#firmwareCard, QFrame#ciCard,
QFrame#commandPanel, QFrame#campaignPanel, QFrame#reportPanel,
QFrame#hardwareMonitorPanel, QFrame#reportSummaryPanel,
QFrame#testResultsPanel, QFrame#serialConsolePanel, QFrame#ciStatusPanel {
    background: #FFFFFF;
    border: 1px solid #D9E1E8;
    border-radius: 0px;
}
QFrame#greenLedCard, QFrame#redLedCard,
QFrame#totalTestsLabelCard, QFrame#passedTestsLabelCard,
QFrame#failedTestsLabelCard, QFrame#skippedTestsLabelCard {
    background: #F7F9FB;
    border: 1px solid #E2E8EE;
    border-radius: 0px;
}
QLabel#dutCardTitle, QLabel#hilCardTitle, QLabel#firmwareCardTitle,
QLabel#ciCardTitle, QLabel#commandTitleLabel, QLabel#campaignTitleLabel,
QLabel#reportActionsTitleLabel, QLabel#hardwareTitleLabel,
QLabel#summaryTitleLabel, QLabel#testResultsTitleLabel,
QLabel#serialConsoleTitleLabel, QLabel#ciPanelTitleLabel {
    color: #1F3042;
    font-size: 10.5pt;
    font-weight: 700;
}
QLabel#dutDetailLabel, QLabel#hilDetailLabel, QLabel#firmwareDetailLabel,
QLabel#lastCiRunNumberLabel, QLabel#hardwareSubtitleLabel,
QLabel#testResultsSubtitleLabel, QLabel#serialConsoleSubtitleLabel,
QLabel#lastCampaignLabel, QLabel#commandHintLabel {
    color: #657589;
    font-size: 8.5pt;
}
QLabel#buildStatusLabel, QLabel#flashStatusLabel, QLabel#ciHilStatusLabel,
QLabel#ciReportsStatusLabel, QLabel#ciFirmwareArtifactStatusLabel {
    font-size: 8pt;
}
QLabel#ciRepositoryLabel, QLabel#lastCiUpdatedLabel {
    color: #657589;
    font-size: 7.5pt;
}
QLabel[state="success"] {
    color: #21633B; background: #EAF5EE;
    border: 1px solid #C9E6D2; border-radius: 0px;
    padding: 3px 7px; font-weight: 700;
}
QLabel[state="failure"] {
    color: #9B2C2C; background: #FCEEEE;
    border: 1px solid #F1CCCC; border-radius: 0px;
    padding: 3px 7px; font-weight: 700;
}
QLabel[state="pending"] {
    color: #875B16; background: #FBF4E5;
    border: 1px solid #EEDDB8; border-radius: 0px;
    padding: 3px 7px; font-weight: 700;
}
QLabel[state="neutral"] {
    color: #526274; background: #EEF2F5;
    border: 1px solid #DFE5EA; border-radius: 0px;
    padding: 3px 7px; font-weight: 600;
}
QLabel#greenLedStateLabel, QLabel#redLedStateLabel {
    font-size: 12pt; font-weight: 800;
    padding: 2px 8px; border-radius: 0px;
    background: #EEF2F5; color: #526274;
}
QLabel#greenLedStateLabel[state="on"] { color: #21633B; background: #EAF5EE; }
QLabel#redLedStateLabel[state="on"] { color: #9B2C2C; background: #FCEEEE; }
QLabel#greenLedStateLabel[state="off"], QLabel#redLedStateLabel[state="off"] {
    color: #526274; background: #EEF2F5;
}
QLabel#totalTestsLabel, QLabel#passedTestsLabel, QLabel#failedTestsLabel,
QLabel#skippedTestsLabel { font-size: 15pt; font-weight: 800; color: #243244; }
QLabel#passedTestsLabel { color: #267346; }
QLabel#failedTestsLabel { color: #A33333; }
QPushButton {
    background: #2F6690; color: #FFFFFF;
    border: 1px solid #2F6690; border-radius: 0px;
    padding: 5px 8px; min-height: 20px;
    font-weight: 600;
}
QPushButton:hover { background: #28577B; border-color: #28577B; }
QPushButton:pressed { background: #204663; }
QPushButton:disabled {
    color: #8A98A8; background: #EDF1F4; border-color: #E3E8ED;
}
QPushButton#redonbutton {
    background: #FCEEEE; color: #9B2C2C; border-color: #F1CCCC;
}
QPushButton#redonbutton:hover { background: #F7DDDD; }
QPushButton#greenonbutton {
    background: #EAF5EE; color: #21633B; border-color: #C9E6D2;
}
QPushButton#greenonbutton:hover { background: #DCEFE3; }
QPushButton#redoffbutton, QPushButton#greenoffbutton,
QPushButton#alloffbutton, QPushButton#openReportsFolderButton,
QPushButton#connectPortsButton {
    background: #EEF2F5; color: #34465A; border-color: #D9E1E8;
}
QPushButton#redoffbutton:hover, QPushButton#greenoffbutton:hover,
QPushButton#alloffbutton:hover, QPushButton#openReportsFolderButton:hover,
QPushButton#connectPortsButton:hover { background: #E3E9EE; }
QPushButton#allonbutton {
    background: #E8F0F8; color: #24577E; border-color: #C9D9E8;
}
QPushButton#allonbutton:hover { background: #DCE9F4; }
QPushButton#generatereportbutton, QPushButton#openHtmlReportButton {
    background: #2F6690; color: #FFFFFF; border-color: #2F6690;
}
QPushButton#refreshCiButton { background: #FFFFFF; color: #24445F; border-color: #D5E0E8; }
QPushButton#refreshCiButton:hover { background: #EDF3F7; }
QPushButton#openCiRunButton { background: #E8F0F8; color: #24577E; border-color: #C9D9E8; }
QTableWidget {
    background: #FFFFFF; alternate-background-color: #F7F9FB;
    border: 1px solid #DCE4EA; border-radius: 0px;
    selection-background-color: #DCEAF5; selection-color: #203247;
    outline: 0; gridline-color: #E9EEF2;
}
QHeaderView::section {
    background: #EDF2F6; color: #34465A; border: none;
    border-bottom: 1px solid #D8E1E8; padding: 6px 7px;
    font-weight: 700; font-size: 8.5pt;
}
QPlainTextEdit#serialConsole {
    background: #1D2B3A; color: #E1E9F0;
    border: 1px solid #314456; border-radius: 0px;
    padding: 7px; font-family: Consolas, "Courier New", monospace;
    font-size: 8.5pt;
}
QScrollBar:vertical { background: #F0F3F6; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #B8C4CE; border-radius: 0px; min-height: 25px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


# -----------------------------------------------------------------------------
# Background workers: opening serial ports, sending commands, querying GitHub
# -----------------------------------------------------------------------------

class SerialOpenWorker(QThread):
    opened = Signal(str, object, str)

    def __init__(self, port_name: str, baudrate: int, parent=None):
        super().__init__(parent)
        self.port_name = port_name
        self.baudrate = baudrate

    def run(self):
        try:
            from tools.serial_connection import open_serial_with_retry

            port = open_serial_with_retry(self.port_name, self.baudrate)
            if port is None:
                raise RuntimeError("Serial helper returned no port.")
            if self.isInterruptionRequested():
                port.close()
                return
            port.reset_input_buffer()
            # The HIL monitor is polled frequently; a short timeout avoids
            # freezing the Qt event loop if the Arduino is temporarily silent.
            if self.port_name == "COM7":
                port.timeout = 0.35
            self.opened.emit(self.port_name, port, "")
        except Exception as error:
            self.opened.emit(self.port_name, None, str(error))


class SerialCommandWorker(QThread):
    # Separate signals let the DUT reply appear before the HIL monitor finishes reading.
    dut_response = Signal(str, float)
    hil_response = Signal(str, float)
    failed = Signal(str)

    def __init__(self, dut_port, hil_port, command: str, parent=None):
        super().__init__(parent)
        self.dut_port = dut_port
        self.hil_port = hil_port
        self.command = command

    def run(self):
        try:
            original_timeout = self.dut_port.timeout
            dut_started = time.perf_counter()
            try:
                # Manual actions should not wait the full 2-second test timeout.
                # A partial reply is still returned by readline() when this expires.
                self.dut_port.timeout = 0.8
                self.dut_port.reset_input_buffer()
                self.dut_port.write((self.command + "\r\n").encode("ascii"))
                self.dut_port.flush()

                response_lines = []
                line = self.dut_port.readline().decode(errors="replace").strip()
                if line:
                    response_lines.append(line)

                # The current STM32 firmware sends ALL ON as two lines, while
                # ALL OFF is one combined line. Do not wait for a nonexistent
                # second line on ALL OFF.
                if self.command == "all on":
                    second_line = self.dut_port.readline().decode(errors="replace").strip()
                    if second_line:
                        response_lines.append(second_line)

                response = "\n".join(response_lines)
                dut_elapsed = time.perf_counter() - dut_started
            finally:
                self.dut_port.timeout = original_timeout

            # Show the STM32 response immediately, without waiting for Arduino.
            self.dut_response.emit(response, dut_elapsed)

            hil_state = ""
            hil_elapsed = 0.0
            if self.hil_port is not None and getattr(self.hil_port, "is_open", False):
                hil_started = time.perf_counter()
                self.hil_port.reset_input_buffer()
                self.hil_port.write(b"READ\n")
                self.hil_port.flush()
                hil_state = self.hil_port.readline().decode(errors="replace").strip()
                hil_elapsed = time.perf_counter() - hil_started

            self.hil_response.emit(hil_state, hil_elapsed)
        except Exception as error:
            self.failed.emit(str(error))


class GitHubStatusWorker(QThread):
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, repository: str, workflow_file: str, branch: str, token: str | None, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.workflow_file = workflow_file
        self.branch = branch
        self.token = token

    def run(self):
        try:
            from tools.github_actions import fetch_latest_workflow_run

            result = fetch_latest_workflow_run(
                repository=self.repository,
                workflow_file=self.workflow_file,
                branch=self.branch,
                token=self.token,
            )
            self.completed.emit(result)
        except Exception as error:
            self.failed.emit(str(error))


# -----------------------------------------------------------------------------
# Dashboard controller
# -----------------------------------------------------------------------------

class DashboardController:
    def __init__(self, app: QApplication):
        self.app = app
        self.dut_serial = None
        self.hil_serial = None
        self._serial_workers: set[SerialOpenWorker] = set()
        self._connecting_ports: set[str] = set()
        self._command_worker: SerialCommandWorker | None = None
        self._github_worker: GitHubStatusWorker | None = None
        self._test_process: QProcess | None = None
        self._current_campaign: dict | None = None
        self._campaign_finalized = False
        self._ci_run_url: str | None = None
        self._last_ci_log_signature = None
        self._ci_config = self._load_ci_config()

        ui_path = DASHBOARD_DIR / "dashboard.ui"
        if not ui_path.exists():
            raise FileNotFoundError(f"Dashboard UI file not found: {ui_path}")

        ui_file = QFile(str(ui_path))
        if not ui_file.open(QFile.ReadOnly):
            raise RuntimeError(f"Cannot open dashboard UI file: {ui_path}")
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        if self.window is None:
            raise RuntimeError(f"Qt could not load dashboard.ui: {loader.errorString()}")

        self._bind_widgets()
        self.labels["ciRepositoryLabel"].setText(self._ci_config["repository"])
        self._apply_styles()
        self._configure_table()
        self._configure_layouts()
        self._connect_signals()

        self.hardware_timer = QTimer(self.window)
        self.hardware_timer.setInterval(1000)
        self.hardware_timer.timeout.connect(self.refresh_hardware_monitor)

        self.ci_timer = QTimer(self.window)
        refresh_seconds = max(120, int(self._ci_config.get("refresh_interval_seconds", 300)))
        self.ci_timer.setInterval(refresh_seconds * 1000)
        self.ci_timer.timeout.connect(self.refresh_ci_status)
        self.ci_timer.start()

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_previous_results()
        self._update_report_actions()
        self._update_controls()

        self.log_message("[DASHBOARD] STM32 HIL Validation Dashboard started")
        self.log_message("[INFO] DUT: Bluetooth COM5 / 9600 baud / STM32 USART6")
        self.log_message("[INFO] HIL: Arduino COM7 / 115200 baud")
        self.log_message(f"[CI] Repository: {self._ci_config['repository']}")
        self.log_message("[CI] Read-only status polling; local test buttons do not start GitHub Actions (workflow trigger: push to main).")

        self.app.aboutToQuit.connect(self.shutdown)
        self.window.showMaximized()
        QTimer.singleShot(350, self.connect_serial_ports)
        QTimer.singleShot(1200, self.refresh_ci_status)

    # ----- UI setup ---------------------------------------------------------

    def _bind_widgets(self):
        def find(widget_type, name):
            widget = self.window.findChild(widget_type, name)
            if widget is None:
                raise RuntimeError(f"Widget '{name}' is missing from dashboard.ui")
            return widget

        button_names = [
            "redonbutton", "redoffbutton", "greenonbutton", "greenoffbutton",
            "allonbutton", "alloffbutton", "runuartbutton", "runhilbutton",
            "generatereportbutton", "openHtmlReportButton", "openReportsFolderButton",
            "connectPortsButton", "refreshCiButton", "openCiRunButton",
        ]
        self.buttons = {name: find(QPushButton, name) for name in button_names}

        label_names = [
            "dutConnectionLabel", "dutDetailLabel", "hilConnectionLabel", "hilDetailLabel",
            "firmwareStatusLabel", "firmwareDetailLabel", "lastCiStatusLabel",
            "lastCiRunNumberLabel", "lastCiUpdatedLabel", "lastCampaignLabel",
            "greenLedStateLabel", "redLedStateLabel", "totalTestsLabel",
            "passedTestsLabel", "failedTestsLabel", "skippedTestsLabel",
            "buildStatusLabel", "flashStatusLabel", "uartTestsStatusLabel",
            "hilTestsStatusLabel", "reportsStatusLabel", "ciHilStatusLabel",
            "ciReportsStatusLabel", "ciFirmwareArtifactStatusLabel", "ciRepositoryLabel",
        ]
        self.labels = {name: find(QLabel, name) for name in label_names}
        self.console = find(QPlainTextEdit, "serialConsole")
        self.results_table = find(QTableWidget, "testResultsTable")

    def _apply_styles(self):
        self.window.setStyleSheet(APP_STYLE)
        self.window.setMinimumSize(1080, 660)

    def _configure_table(self):
        table = self.results_table
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Test name", "Campaign", "Status", "Duration"])
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.setMinimumHeight(105)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.ElideMiddle)
        table.verticalHeader().setDefaultSectionSize(28)
        table.horizontalHeader().setFixedHeight(32)
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(2000)

    def _configure_layouts(self):
        """Give the serial console more vertical room while keeping the table usable."""
        bottom_row = self.window.findChild(QHBoxLayout, "bottomRowLayout")
        if bottom_row is not None:
            bottom_row.setStretch(0, 7)
            bottom_row.setStretch(1, 2)

        right_layout = self.window.findChild(QVBoxLayout, "rightPanelLayout")
        if right_layout is not None:
            right_layout.setSpacing(6)
            right_layout.setStretch(0, 0)  # connection / LED summary row
            right_layout.setStretch(1, 1)  # test results table
            right_layout.setStretch(2, 2)  # console + CI details

        # The summary row needs enough height for the LED states and all four
        # campaign counters. The table gives up a little height to preserve the
        # console while preventing text from being clipped at the bottom.
        minimum_heights = {
            "hardwareMonitorPanel": 118,
            "reportSummaryPanel": 120,
            "testResultsPanel": 160,
            "serialConsolePanel": 195,
            "ciStatusPanel": 195,
            "greenLedCard": 60,
            "redLedCard": 60,
            "totalTestsLabelCard": 54,
            "passedTestsLabelCard": 54,
            "failedTestsLabelCard": 54,
            "skippedTestsLabelCard": 54,
        }
        for name, height in minimum_heights.items():
            panel = self.window.findChild(QFrame, name)
            if panel is not None:
                panel.setMinimumHeight(height)

        # Explicit line heights keep OFF and the campaign counts fully visible.
        label_heights = {
            "greenLedStateLabel": 22,
            "redLedStateLabel": 22,
            "totalTestsLabel": 24,
            "passedTestsLabel": 24,
            "failedTestsLabel": 24,
            "skippedTestsLabel": 24,
            "totalTestsLabelCaption": 16,
            "passedTestsLabelCaption": 16,
            "failedTestsLabelCaption": 16,
            "skippedTestsLabelCaption": 16,
        }
        for name, height in label_heights.items():
            label = self.window.findChild(QLabel, name)
            if label is not None:
                label.setMinimumHeight(height)
                label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        for name in ("greenLedStateLabel", "redLedStateLabel"):
            label = self.window.findChild(QLabel, name)
            if label is not None:
                label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    def _connect_signals(self):
        self.buttons["redonbutton"].clicked.connect(lambda: self.send_dut_command("red on"))
        self.buttons["redoffbutton"].clicked.connect(lambda: self.send_dut_command("red off"))
        self.buttons["greenonbutton"].clicked.connect(lambda: self.send_dut_command("green on"))
        self.buttons["greenoffbutton"].clicked.connect(lambda: self.send_dut_command("green off"))
        self.buttons["allonbutton"].clicked.connect(lambda: self.send_dut_command("all on"))
        self.buttons["alloffbutton"].clicked.connect(lambda: self.send_dut_command("all off"))

        self.buttons["runuartbutton"].clicked.connect(self.run_uart_tests)
        self.buttons["runhilbutton"].clicked.connect(self.run_hil_tests)
        self.buttons["generatereportbutton"].clicked.connect(self.generate_report)
        self.buttons["openHtmlReportButton"].clicked.connect(self.open_html_report)
        self.buttons["openReportsFolderButton"].clicked.connect(self.open_reports_folder)
        self.buttons["connectPortsButton"].clicked.connect(self.connect_serial_ports)
        self.buttons["refreshCiButton"].clicked.connect(self.refresh_ci_status)
        self.buttons["openCiRunButton"].clicked.connect(self.open_latest_ci_run)

    # ----- General helpers --------------------------------------------------

    def _load_ci_config(self) -> dict:
        config = dict(DEFAULT_CI_CONFIG)
        if CI_CONFIG_PATH.exists():
            try:
                user_config = json.loads(CI_CONFIG_PATH.read_text(encoding="utf-8"))
                if isinstance(user_config, dict):
                    config.update(user_config)
            except (OSError, json.JSONDecodeError) as error:
                print(f"Could not read {CI_CONFIG_PATH}: {error}")
        config["repository"] = str(config.get("repository", "")).strip()
        config["workflow_file"] = str(config.get("workflow_file", "hil-ci.yml")).strip()
        config["branch"] = str(config.get("branch", "main")).strip()
        return config

    def log_message(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.appendPlainText(f"[{timestamp}] {message}")

    def set_status(self, label_name: str, text: str, state: str = "neutral"):
        label = self.labels[label_name]
        label.setText(str(text))
        label.setProperty("state", state)
        label.style().unpolish(label)
        label.style().polish(label)
        label.update()

    @staticmethod
    def port_is_open(port) -> bool:
        return port is not None and bool(getattr(port, "is_open", True))

    def close_serial_port(self, port):
        if port is None:
            return
        try:
            if self.port_is_open(port):
                port.close()
        except Exception as error:
            self.log_message(f"[SERIAL] Error while closing port: {error}")

    def _is_busy(self) -> bool:
        process_running = self._current_campaign is not None or (
            self._test_process is not None
            and self._test_process.state() != QProcess.NotRunning
        )
        command_running = self._command_worker is not None
        return process_running or command_running

    def _update_controls(self):
        busy = self._is_busy() or bool(self._connecting_ports)
        dut_ready = self.port_is_open(self.dut_serial)
        hil_ready = self.port_is_open(self.hil_serial)

        for name in ("redonbutton", "redoffbutton", "greenonbutton", "greenoffbutton", "allonbutton", "alloffbutton"):
            self.buttons[name].setEnabled(not busy and dut_ready)
        self.buttons["runuartbutton"].setEnabled(not busy and dut_ready)
        self.buttons["runhilbutton"].setEnabled(not busy and dut_ready and hil_ready)
        self.buttons["generatereportbutton"].setEnabled(not busy and dut_ready and hil_ready)
        self.buttons["connectPortsButton"].setEnabled(not busy and not self._connecting_ports)
        self.buttons["refreshCiButton"].setEnabled(self._github_worker is None)

    # ----- Serial connection management ------------------------------------

    def connect_serial_ports(self):
        if self._is_busy() or self._connecting_ports:
            return
        self.log_message("[SERIAL] Reconnecting both hardware links...")
        self.hardware_timer.stop()
        self.close_serial_port(self.dut_serial)
        self.close_serial_port(self.hil_serial)
        self.dut_serial = None
        self.hil_serial = None
        self.update_hardware_monitor("")
        self._start_serial_connections([("COM5", 9600), ("COM7", 115200)])

    def _start_serial_connections(self, ports: list[tuple[str, int]]):
        if not ports:
            self._update_controls()
            return

        for port_name, baudrate in ports:
            if port_name in self._connecting_ports:
                continue
            self._connecting_ports.add(port_name)
            if port_name == "COM5":
                self.set_status("dutConnectionLabel", "Connecting...", "pending")
            else:
                self.set_status("hilConnectionLabel", "Connecting...", "pending")

            worker = SerialOpenWorker(port_name, baudrate, self.window)
            worker.opened.connect(self._on_serial_opened)
            worker.finished.connect(lambda w=worker: self._release_serial_worker(w))
            self._serial_workers.add(worker)
            worker.start()

        self._update_controls()

    def _release_serial_worker(self, worker: SerialOpenWorker):
        self._serial_workers.discard(worker)
        worker.deleteLater()

    def _on_serial_opened(self, port_name: str, port, error: str):
        if port_name == "COM5":
            self.close_serial_port(self.dut_serial)
            self.dut_serial = port
            if self.port_is_open(port):
                self.set_status("dutConnectionLabel", "Connected", "success")
                self.log_message("[SERIAL] Bluetooth DUT connected on COM5 at 9600 baud")
            else:
                self.set_status("dutConnectionLabel", "Disconnected", "failure")
                self.log_message(f"[SERIAL] Cannot open Bluetooth COM5: {error}")
        elif port_name == "COM7":
            self.close_serial_port(self.hil_serial)
            self.hil_serial = port
            if self.port_is_open(port):
                self.set_status("hilConnectionLabel", "Connected", "success")
                self.log_message("[SERIAL] Arduino HIL connected on COM7 at 115200 baud")
            else:
                self.set_status("hilConnectionLabel", "Disconnected", "failure")
                self.log_message(f"[SERIAL] Cannot open HIL COM7: {error}")
                self.update_hardware_monitor("")

        self._connecting_ports.discard(port_name)
        if not self._connecting_ports and self.port_is_open(self.hil_serial):
            self.hardware_timer.start()
        self._update_controls()

    # ----- Hardware monitor -------------------------------------------------

    def read_hil_state(self) -> str:
        if not self.port_is_open(self.hil_serial):
            return ""
        try:
            self.hil_serial.reset_input_buffer()
            self.hil_serial.write(b"READ\n")
            self.hil_serial.flush()
            return self.hil_serial.readline().decode(errors="replace").strip()
        except Exception as error:
            self.log_message(f"[HIL] Read error: {error}")
            return ""

    def update_hardware_monitor(self, hil_state: str):
        if not hil_state:
            self.labels["greenLedStateLabel"].setText("N/A")
            self.labels["redLedStateLabel"].setText("N/A")
            self.labels["greenLedStateLabel"].setProperty("state", "neutral")
            self.labels["redLedStateLabel"].setProperty("state", "neutral")
            return

        green = re.search(r"GREEN\s*=\s*([01])", hil_state)
        red = re.search(r"RED\s*=\s*([01])", hil_state)
        green_value = "ON" if green and green.group(1) == "1" else "OFF" if green else "N/A"
        red_value = "ON" if red and red.group(1) == "1" else "OFF" if red else "N/A"

        self.labels["greenLedStateLabel"].setText(green_value)
        self.labels["redLedStateLabel"].setText(red_value)
        self.labels["greenLedStateLabel"].setProperty("state", green_value.lower())
        self.labels["redLedStateLabel"].setProperty("state", red_value.lower())

        for name in ("greenLedStateLabel", "redLedStateLabel"):
            label = self.labels[name]
            label.style().unpolish(label)
            label.style().polish(label)

    def refresh_hardware_monitor(self):
        if self._command_worker is not None and self._command_worker.isRunning():
            return
        if self.port_is_open(self.hil_serial):
            self.update_hardware_monitor(self.read_hil_state())
        else:
            self.update_hardware_monitor("")

    # ----- Manual DUT commands ---------------------------------------------

    def send_dut_command(self, command: str):
        if self._is_busy():
            return
        if not self.port_is_open(self.dut_serial):
            self.log_message("[ERROR] Bluetooth DUT is not connected. Check COM5.")
            return

        self.log_message(f"[TX] {command}")
        self.hardware_timer.stop()
        self._command_worker = SerialCommandWorker(
            self.dut_serial, self.hil_serial, command, self.window
        )
        self._command_worker.dut_response.connect(self._on_dut_response)
        self._command_worker.hil_response.connect(self._on_hil_response)
        self._command_worker.failed.connect(self._on_command_failed)
        self._command_worker.finished.connect(self._on_command_finished)
        self._update_controls()
        self._command_worker.start()

    def _on_dut_response(self, response: str, elapsed: float):
        self.log_message(f"[RX] {response if response else 'No DUT response within 0.8 s'}")
        self.log_message(f"[TIMING] STM32 response: {elapsed:.3f} s")

    def _on_hil_response(self, hil_state: str, elapsed: float):
        self.log_message(f"[HIL] {hil_state if hil_state else 'No HIL response'}")
        self.log_message(f"[TIMING] Arduino HIL read: {elapsed:.3f} s")
        self.update_hardware_monitor(hil_state)

    def _on_command_failed(self, error: str):
        self.log_message(f"[ERROR] DUT command failed: {error}")

    def _on_command_finished(self):
        worker = self._command_worker
        self._command_worker = None
        if worker is not None:
            worker.deleteLater()
        if self.port_is_open(self.hil_serial):
            self.hardware_timer.start()
        self._update_controls()

    # ----- Test results and summaries --------------------------------------

    def update_test_summary(self, total: int, passed: int, failed: int, skipped: int):
        self.labels["totalTestsLabel"].setText(str(total))
        self.labels["passedTestsLabel"].setText(str(passed))
        self.labels["failedTestsLabel"].setText(str(failed))
        self.labels["skippedTestsLabel"].setText(str(skipped))

    def load_test_results(self, xml_path: Path, campaign_type: str) -> bool:
        if not xml_path.exists():
            self.log_message(f"[TEST] XML result file not found: {xml_path}")
            return False

        try:
            root = ET.parse(xml_path).getroot()
        except (ET.ParseError, OSError) as error:
            self.log_message(f"[TEST] Cannot parse XML report: {error}")
            return False

        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(0)
        total = passed = failed = skipped = 0

        for testcase in root.iter("testcase"):
            total += 1
            test_name = testcase.get("name", "Unknown test")
            duration_text = testcase.get("time", "0")
            try:
                duration = float(duration_text)
            except (TypeError, ValueError):
                duration = 0.0

            if testcase.find("failure") is not None:
                status = "FAIL"
                failed += 1
            elif testcase.find("error") is not None:
                status = "ERROR"
                failed += 1
            elif testcase.find("skipped") is not None:
                status = "SKIPPED"
                skipped += 1
            else:
                status = "PASS"
                passed += 1

            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            test_name_item = QTableWidgetItem(test_name)
            test_name_item.setToolTip(test_name)
            items = [
                test_name_item,
                QTableWidgetItem(campaign_type),
                QTableWidgetItem(status),
                QTableWidgetItem(f"{duration:.2f} s"),
            ]
            items[1].setTextAlignment(Qt.AlignCenter)
            items[2].setTextAlignment(Qt.AlignCenter)
            items[3].setTextAlignment(Qt.AlignCenter)
            if status == "PASS":
                items[2].setForeground(QColor("#15803D"))
            elif status in ("FAIL", "ERROR"):
                items[2].setForeground(QColor("#B91C1C"))
            else:
                items[2].setForeground(QColor("#A16207"))
            for column, table_item in enumerate(items):
                self.results_table.setItem(row, column, table_item)

        self.results_table.setSortingEnabled(True)
        self.update_test_summary(total, passed, failed, skipped)
        return True

    def _load_previous_results(self):
        candidates = [
            ("FULL", REPORTS_DIR / "results.xml"),
            ("UART", REPORTS_DIR / "dashboard_uart.xml"),
            ("HIL", REPORTS_DIR / "dashboard_hil.xml"),
        ]
        existing = [(kind, path) for kind, path in candidates if path.exists()]
        if not existing:
            self.update_test_summary(0, 0, 0, 0)
            self.labels["lastCampaignLabel"].setText("No previous local campaign")
            return

        campaign_type, xml_path = max(existing, key=lambda entry: entry[1].stat().st_mtime)
        if self.load_test_results(xml_path, campaign_type):
            modified = datetime.fromtimestamp(xml_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            self.labels["lastCampaignLabel"].setText(
                f"{campaign_type}  |  {self.results_table.rowCount()} tests  |  {modified}"
            )
            self.log_message(f"[TEST] Loaded previous {campaign_type} results from {xml_path.name}")

    # ----- Pytest campaigns (asynchronous QProcess) -------------------------

    def run_uart_tests(self):
        self.run_pytest_campaign(
            title="[TEST] Starting UART regression campaign...",
            test_paths=[
                "tests/test_leds.py",
                "tests/test_invalid_commands.py",
                "tests/test_robustness.py",
            ],
            xml_name="dashboard_uart.xml",
            close_dut=True,
            close_hil=False,
            generate_html=False,
            test_type="UART",
        )

    def run_hil_tests(self):
        self.run_pytest_campaign(
            title="[TEST] Starting HIL campaign...",
            test_paths=["tests/test_hil.py"],
            xml_name="dashboard_hil.xml",
            close_dut=True,
            close_hil=True,
            generate_html=False,
            test_type="HIL",
        )

    def generate_report(self):
        self.run_pytest_campaign(
            title="[REPORT] Starting complete validation campaign...",
            test_paths=None,
            xml_name="results.xml",
            close_dut=True,
            close_hil=True,
            generate_html=True,
            test_type="FULL",
        )

    def run_pytest_campaign(
        self,
        title: str,
        test_paths: list[str] | None,
        xml_name: str,
        close_dut: bool,
        close_hil: bool,
        generate_html: bool,
        test_type: str,
    ):
        if self._is_busy() or self._connecting_ports:
            self.log_message("[TEST] Another operation is already running.")
            return
        if not self.port_is_open(self.dut_serial):
            self.log_message("[TEST] Bluetooth DUT is not connected; campaign not started.")
            return
        if close_hil and not self.port_is_open(self.hil_serial):
            self.log_message("[TEST] Arduino HIL monitor is not connected; campaign not started.")
            return

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        xml_path = REPORTS_DIR / xml_name
        html_path = REPORTS_DIR / "test_report.html"
        xml_path.unlink(missing_ok=True)
        if generate_html:
            html_path.unlink(missing_ok=True)

        self.log_message(title)
        if close_dut:
            self.close_serial_port(self.dut_serial)
            self.dut_serial = None
            self.set_status("dutConnectionLabel", "Released for tests", "pending")
        if close_hil:
            self.hardware_timer.stop()
            self.close_serial_port(self.hil_serial)
            self.hil_serial = None
            self.set_status("hilConnectionLabel", "Released for tests", "pending")

        if test_type == "UART":
            self.set_status("uartTestsStatusLabel", "UART: Running", "pending")
        elif test_type == "HIL":
            self.set_status("hilTestsStatusLabel", "HIL: Running", "pending")
        else:
            self.set_status("uartTestsStatusLabel", "UART: Included", "pending")
            self.set_status("hilTestsStatusLabel", "HIL: Included", "pending")
            self.set_status("reportsStatusLabel", "Reports: Generating", "pending")

        args = ["-m", "pytest"]
        if test_paths:
            args.extend(test_paths)
        args.extend(["-q", f"--junitxml=reports/{xml_name}"])
        if generate_html:
            args.extend(["--html=reports/test_report.html", "--self-contained-html"])

        self._current_campaign = {
            "type": test_type,
            "xml_path": xml_path,
            "html_path": html_path,
            "generate_html": generate_html,
            "reopen_dut": close_dut,
            "reopen_hil": close_hil,
            "started_at": datetime.now(),
        }
        self._campaign_finalized = False

        process = QProcess(self.window)
        process.setWorkingDirectory(str(PROJECT_ROOT))
        process.setProgram(sys.executable)
        process.setArguments(args)
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyReadStandardOutput.connect(self._read_test_output)
        process.finished.connect(self._on_test_process_finished)
        process.errorOccurred.connect(self._on_test_process_error)
        process.started.connect(lambda: self.log_message("[TEST] Pytest process started"))
        self._test_process = process
        self._update_controls()
        self.log_message("[TEST] Command: " + " ".join([sys.executable] + args))
        process.start()

    def _read_test_output(self):
        if self._test_process is None:
            return
        data = bytes(self._test_process.readAllStandardOutput()).decode(errors="replace")
        if data:
            for line in data.replace("\r", "").splitlines():
                if line.strip():
                    self.log_message(line)

    def _on_test_process_finished(self, exit_code: int, exit_status):
        self._finalize_test_campaign(exit_code, "" if exit_code == 0 else f"Pytest exit code {exit_code}")

    def _on_test_process_error(self, process_error):
        if self._test_process is None:
            return
        if process_error == QProcess.FailedToStart:
            self._finalize_test_campaign(-1, self._test_process.errorString())

    def _finalize_test_campaign(self, exit_code: int, error_message: str):
        if self._campaign_finalized or self._current_campaign is None:
            return
        self._campaign_finalized = True
        self._read_test_output()
        campaign = self._current_campaign
        xml_loaded = self.load_test_results(campaign["xml_path"], campaign["type"])
        success = exit_code == 0 and xml_loaded

        elapsed = (datetime.now() - campaign["started_at"]).total_seconds()
        self.labels["lastCampaignLabel"].setText(
            f"{campaign['type']}  |  {self.results_table.rowCount()} tests  |  {elapsed:.1f} s"
        )

        if campaign["type"] == "UART":
            self.set_status(
                "uartTestsStatusLabel",
                "UART: Passed" if success else "UART: Failed",
                "success" if success else "failure",
            )
        elif campaign["type"] == "HIL":
            self.set_status(
                "hilTestsStatusLabel",
                "HIL: Passed" if success else "HIL: Failed",
                "success" if success else "failure",
            )
        else:
            if success:
                self.set_status("uartTestsStatusLabel", "UART: Passed", "success")
                self.set_status("hilTestsStatusLabel", "HIL: Passed", "success")
            else:
                self.set_status("uartTestsStatusLabel", "UART: See results", "pending")
                self.set_status("hilTestsStatusLabel", "HIL: See results", "pending")
            html_exists = campaign["html_path"].exists()
            self.set_status(
                "reportsStatusLabel",
                "Reports: Generated" if html_exists else "Reports: HTML missing",
                "success" if html_exists else "failure",
            )
            if html_exists:
                self.log_message(f"[REPORT] HTML report generated: {campaign['html_path']}")

        if success:
            self.log_message(f"[TEST] {campaign['type']} campaign PASSED")
        else:
            self.log_message(f"[TEST] {campaign['type']} campaign FAILED")
            if error_message:
                self.log_message(f"[TEST] {error_message}")

        process = self._test_process
        self._test_process = None
        self._current_campaign = None
        if process is not None:
            process.deleteLater()

        ports_to_reopen = []
        if campaign["reopen_dut"]:
            ports_to_reopen.append(("COM5", 9600))
        if campaign["reopen_hil"]:
            ports_to_reopen.append(("COM7", 115200))
        if ports_to_reopen:
            QTimer.singleShot(700, lambda p=ports_to_reopen: self._start_serial_connections(p))
        else:
            self._update_controls()

        self._update_report_actions()

    # ----- Local reports ----------------------------------------------------

    def _update_report_actions(self):
        html_exists = (REPORTS_DIR / "test_report.html").exists()
        self.buttons["openHtmlReportButton"].setEnabled(html_exists)
        self.buttons["openReportsFolderButton"].setEnabled(REPORTS_DIR.exists())
        if html_exists and self.labels["reportsStatusLabel"].text() in (
            "Reports: Not generated", "Reports: HTML missing"
        ):
            self.set_status("reportsStatusLabel", "Reports: HTML available", "success")

    def open_html_report(self):
        report_path = REPORTS_DIR / "test_report.html"
        if not report_path.exists():
            self.log_message("[REPORT] HTML report does not exist yet.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(report_path.resolve())))

    def open_reports_folder(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(REPORTS_DIR.resolve())))

    # ----- GitHub Actions status -------------------------------------------

    def refresh_ci_status(self):
        if self._github_worker is not None and self._github_worker.isRunning():
            return
        repository = self._ci_config.get("repository", "")
        workflow_file = self._ci_config.get("workflow_file", "hil-ci.yml")
        branch = self._ci_config.get("branch", "main")
        if not repository:
            self.set_status("lastCiStatusLabel", "Configure CI repository", "pending")
            return

        self.set_status("lastCiStatusLabel", "Refreshing...", "pending")
        self.buttons["refreshCiButton"].setEnabled(False)
        worker = GitHubStatusWorker(
            repository,
            workflow_file,
            branch,
            os.environ.get("GITHUB_TOKEN"),
            self.window,
        )
        worker.completed.connect(self._on_ci_status_loaded)
        worker.failed.connect(self._on_ci_status_failed)
        worker.finished.connect(lambda w=worker: self._release_ci_worker(w))
        self._github_worker = worker
        worker.start()

    def _release_ci_worker(self, worker: GitHubStatusWorker):
        if self._github_worker is worker:
            self._github_worker = None
        worker.deleteLater()
        self._update_controls()

    @staticmethod
    def _run_status(run: dict) -> tuple[str, str]:
        status = (run.get("status") or "unknown").lower()
        conclusion = (run.get("conclusion") or "").lower()
        if status != "completed":
            if status in ("queued", "requested", "waiting", "pending"):
                return "Queued", "pending"
            if status == "in_progress":
                return "In progress", "pending"
            return status.replace("_", " ").title(), "neutral"
        mapping = {
            "success": ("Passed", "success"),
            "failure": ("Failed", "failure"),
            "cancelled": ("Cancelled", "failure"),
            "timed_out": ("Timed out", "failure"),
            "action_required": ("Action required", "pending"),
            "neutral": ("Neutral", "neutral"),
            "skipped": ("Skipped", "neutral"),
        }
        return mapping.get(conclusion, (conclusion.title() or "Completed", "neutral"))

    @staticmethod
    def _find_step(jobs: list[dict], name_fragment: str):
        fragment = name_fragment.casefold()
        for job in jobs:
            for step in job.get("steps", []):
                if fragment in step.get("name", "").casefold():
                    return step
        return None

    @staticmethod
    def _step_status(step: dict | None, run: dict) -> tuple[str, str]:
        if step is None:
            if run.get("status") in ("queued", "in_progress"):
                return "Waiting", "pending"
            if run.get("conclusion") == "cancelled":
                return "Not started", "neutral"
            return "Not reported", "neutral"
        status = (step.get("status") or "").lower()
        conclusion = (step.get("conclusion") or "").lower()
        if status != "completed":
            if status == "in_progress":
                return "Running", "pending"
            return "Queued", "pending"
        mapping = {
            "success": ("Passed", "success"),
            "failure": ("Failed", "failure"),
            "cancelled": ("Cancelled", "failure"),
            "skipped": ("Skipped", "neutral"),
            "timed_out": ("Timed out", "failure"),
            "neutral": ("Neutral", "neutral"),
        }
        return mapping.get(conclusion, (conclusion.title() or "Completed", "neutral"))

    def _on_ci_status_loaded(self, result: dict):
        run = result.get("run")
        if not run:
            self.set_status("lastCiStatusLabel", "No workflow runs", "neutral")
            self.set_status("firmwareStatusLabel", "Not verified", "neutral")
            self.labels["firmwareDetailLabel"].setText("No workflow run is available for this branch")
            self.labels["lastCiRunNumberLabel"].setText("No run found on the configured branch")
            self.labels["lastCiUpdatedLabel"].setText("Last update: no workflow run returned")
            self._ci_run_url = None
            self.buttons["openCiRunButton"].setEnabled(False)
            self.set_status("buildStatusLabel", "Build: Not reported", "neutral")
            self.set_status("flashStatusLabel", "Flash: Not reported", "neutral")
            self.set_status("ciHilStatusLabel", "HIL tests: Not reported", "neutral")
            self.set_status("ciReportsStatusLabel", "Report artifacts: Not reported", "neutral")
            self.set_status("ciFirmwareArtifactStatusLabel", "Firmware artifact: Not reported", "neutral")
            return

        run_text, run_state = self._run_status(run)
        self.set_status("lastCiStatusLabel", run_text, run_state)
        self.labels["lastCiRunNumberLabel"].setText(f"Run #{run.get('run_number', '?')}")
        updated = run.get("updated_at") or run.get("created_at") or run.get("run_started_at") or ""
        try:
            updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00")).astimezone()
            updated_text = updated_dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            updated_text = updated or "time unavailable"
        sha = (run.get("head_sha") or "")[:7]
        branch = run.get("head_branch") or self._ci_config.get("branch", "main")
        self.labels["lastCiUpdatedLabel"].setText(f"{branch}  |  {sha}  |  {updated_text}")

        self._ci_run_url = run.get("html_url")
        self.buttons["openCiRunButton"].setEnabled(bool(self._ci_run_url))

        jobs = result.get("jobs", [])
        build_text, build_state = self._step_status(self._find_step(jobs, "Build firmware with Keil"), run)
        flash_text, flash_state = self._step_status(self._find_step(jobs, "Flash STM32 firmware"), run)
        hil_text, hil_state = self._step_status(self._find_step(jobs, "Run STM32 HIL tests"), run)
        report_text, report_state = self._step_status(self._find_step(jobs, "Upload test reports"), run)
        firmware_artifact_text, firmware_artifact_state = self._step_status(
            self._find_step(jobs, "Upload validated firmware"), run
        )

        self.set_status("buildStatusLabel", f"Build: {build_text}", build_state)
        self.set_status("flashStatusLabel", f"Flash: {flash_text}", flash_state)
        self.set_status("ciHilStatusLabel", f"HIL tests: {hil_text}", hil_state)
        self.set_status("ciReportsStatusLabel", f"Report artifacts: {report_text}", report_state)
        self.set_status(
            "ciFirmwareArtifactStatusLabel",
            f"Firmware artifact: {firmware_artifact_text}",
            firmware_artifact_state,
        )

        if build_text == "Passed" and flash_text == "Passed":
            self.set_status("firmwareStatusLabel", "Built + flashed", "success")
            self.labels["firmwareDetailLabel"].setText("Keil build and STM32 flash steps passed")
        elif "Failed" in (build_text, flash_text) or "Timed out" in (build_text, flash_text):
            self.set_status("firmwareStatusLabel", "Pipeline failed", "failure")
            self.labels["firmwareDetailLabel"].setText("Check the Build and Flash steps in GitHub Actions")
        elif run_text == "In progress" or run_text == "Queued":
            self.set_status("firmwareStatusLabel", "Pipeline running", "pending")
            self.labels["firmwareDetailLabel"].setText("Build and flash results are not final yet")
        else:
            self.set_status("firmwareStatusLabel", "Not verified", "neutral")
            self.labels["firmwareDetailLabel"].setText("No successful build and flash result is available")

        # Avoid repeating the same old run status every five-minute refresh.
        log_signature = (run.get("id"), run.get("status"), run.get("conclusion"))
        if log_signature != self._last_ci_log_signature:
            self.log_message(f"[CI] Latest workflow run #{run.get('run_number', '?')}: {run_text}")
            if run.get("conclusion") == "cancelled":
                self.log_message("[CI] This run was cancelled earlier; status check did not launch or restart it.")
            self._last_ci_log_signature = log_signature

    def _on_ci_status_failed(self, error: str):
        self.set_status("lastCiStatusLabel", "Unavailable", "failure")
        self.labels["lastCiUpdatedLabel"].setText("Last update: GitHub status could not be retrieved")
        self.set_status("buildStatusLabel", "Build: Unavailable", "neutral")
        self.set_status("flashStatusLabel", "Flash: Unavailable", "neutral")
        self.set_status("ciHilStatusLabel", "HIL tests: Unavailable", "neutral")
        self.set_status("ciReportsStatusLabel", "Report artifacts: Unavailable", "neutral")
        self.set_status("ciFirmwareArtifactStatusLabel", "Firmware artifact: Unavailable", "neutral")
        self.log_message(f"[CI] {error}")

    def open_latest_ci_run(self):
        if self._ci_run_url:
            QDesktopServices.openUrl(QUrl(self._ci_run_url))

    # ----- Shutdown ---------------------------------------------------------

    def shutdown(self):
        self.hardware_timer.stop()
        self.ci_timer.stop()
        if self._test_process is not None and self._test_process.state() != QProcess.NotRunning:
            self._test_process.terminate()
            if not self._test_process.waitForFinished(1500):
                self._test_process.kill()
                self._test_process.waitForFinished(1500)
        if self._command_worker is not None and self._command_worker.isRunning():
            self._command_worker.wait(6000)
        for worker in list(self._serial_workers):
            worker.requestInterruption()
            worker.wait(10000)
        if self._github_worker is not None and self._github_worker.isRunning():
            self._github_worker.wait(12000)
        self.close_serial_port(self.dut_serial)
        self.close_serial_port(self.hil_serial)


def main():
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    app = QApplication(sys.argv)
    app.setApplicationName("STM32 HIL Validation Dashboard")
    controller = DashboardController(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
