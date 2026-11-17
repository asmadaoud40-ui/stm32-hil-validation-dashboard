# STM32 HIL Validation Dashboard

An automated Hardware-in-the-Loop (HIL) validation platform for an STM32-based embedded system. The project combines a PySide6 graphical dashboard, Bluetooth serial communication, Arduino-based GPIO monitoring, automated pytest campaigns, and a GitHub Actions CI/CD pipeline.

## System Architecture

- **PC → STM32 DUT:** Python, pytest, and the dashboard send commands through Bluetooth on COM5 at 9600 baud. The Bluetooth module is connected to STM32 USART6.
- **STM32 → PC:** command responses are returned through USART6 and the Bluetooth serial connection.
- **GPIO observation:** an Arduino HIL observer monitors the STM32 GPIO states and communicates with the PC through COM7 at 115200 baud.
- **Automated validation:** pytest validates command responses and compares them with the physical GPIO states reported by the Arduino during HIL tests.
- **CI/CD pipeline:** GitHub Actions runs on pushes to `main` using a self-hosted Windows runner. The workflow builds the firmware with Keil, flashes the STM32 using STM32CubeProgrammer, executes automated tests, and uploads test reports and validated firmware artifacts.

## Dashboard Overview

The PySide6 application provides a centralized interface for controlling, monitoring, and validating the embedded system.

### Main Features

- Manual control of Red, Green, and All LEDs through Bluetooth.
- Live monitoring of STM32 GPIO states through the Arduino HIL observer.
- Independent UART and HIL test campaigns.
- Full regression test campaign.
- Real-time serial communication console.
- Test result visualization with execution status and duration.
- Automatic generation and access to HTML and JUnit XML reports.
- GitHub Actions integration to monitor the latest CI/CD run, including Build, Flash, HIL Tests, and report and firmware artifact upload statuses.
- Hardware reconnection and GitHub status refresh controls.

![STM32 HIL Validation Dashboard](https://github.com/user-attachments/assets/753dfbb4-c99e-461f-9416-d11e988d9acd)

## Project Structure

```text
Embedded_Test_Bench_Test/
├── .github/
│   └── workflows/
│       └── hil-ci.yml
├── dashboard/
│   ├── dashboard.ui
│   ├── main.py
│   └── ci_config.json
├── firmware/
│   └── Embedded_Test_Bench/
├── hil/
│   └── arduino_hil_observer.ino
├── reports/
├── tests/
├── tools/
│   ├── serial_connection.py
│   ├── serial_debug.py
│   ├── serial_dual_port.py
│   └── github_actions.py
├── requirements.txt
├── requirements-dashboard.txt
└── pytest.ini
```

## Hardware Configuration

| Connection | PC Port | Baud Rate | Purpose |
|---|---:|---:|---|
| Bluetooth module ↔ STM32 USART6 | COM5 | 9600 | DUT commands and responses |
| Arduino HIL observer | COM7 | 115200 | Physical GPIO state monitoring |

The dashboard manages serial port connections and releases the required ports before launching test campaigns. Connections are restored after the campaigns complete.

## Software Requirements

- Python 3.13
- STM32 development board
- Arduino board configured as the HIL GPIO observer
- Bluetooth serial module
- Keil MDK-ARM
- STM32CubeProgrammer
- GitHub Actions self-hosted Windows runner

## Installation

From the project root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dashboard and test dependencies:

```powershell
python -m pip install -r requirements-dashboard.txt
```

## Launch the Dashboard

From the project root:

```powershell
python -u dashboard\main.py
```

The dashboard connects to the STM32 DUT through COM5 and the Arduino HIL observer through COM7.

## Automated Test Campaigns

All test commands are executed from the project root with the hardware bench connected.

### UART Test Campaign

Validates LED commands, invalid commands, and communication robustness.

```powershell
python -m pytest tests/test_leds.py tests/test_invalid_commands.py tests/test_robustness.py -q
```

### HIL Test Campaign

Validates STM32 command responses against the physical GPIO states monitored by the Arduino.

```powershell
python -m pytest tests/test_hil.py -q
```

### Full Regression Campaign

Executes the complete test suite and generates HTML and JUnit XML reports.

```powershell
python -m pytest -q --html=reports/test_report.html --self-contained-html --junitxml=reports/results.xml
```

The test suite contains 21 test cases:

| Test Category | Test Cases |
|---|---:|
| HIL | 6 |
| Invalid commands | 6 |
| LED commands | 6 |
| Robustness | 3 |
| **Total** | **21** |

## CI/CD Pipeline

The GitHub Actions workflow is defined in:

```text
.github/workflows/hil-ci.yml
```

The workflow is triggered by pushes to the `main` branch and executes on a self-hosted Windows runner.

### Pipeline Stages

1. Repository checkout.
2. Python environment setup and dependency installation.
3. Firmware compilation using Keil MDK-ARM.
4. STM32 firmware flashing using STM32CubeProgrammer.
5. Automated pytest execution.
6. Test report artifact upload.
7. Validated firmware artifact upload after successful execution.

### GitHub Actions Artifacts

The workflow generates and uploads:

- `hil-test-reports`: HTML and JUnit XML test reports.
- `validated-firmware`: compiled firmware files, including HEX and AXF artifacts.

The dashboard provides read-only monitoring of the latest GitHub Actions execution. Local test campaign buttons execute pytest on the PC and do not trigger GitHub Actions.

For private repository access, the dashboard uses a locally configured `GITHUB_TOKEN` environment variable with the required read permissions. The token must never be committed to the repository.

## Generated Reports

The project generates the following reports:

| File | Description |
|---|---|
| `reports/dashboard_uart.xml` | UART campaign results |
| `reports/dashboard_hil.xml` | HIL campaign results |
| `reports/results.xml` | Full regression JUnit XML report |
| `reports/test_report.html` | Self-contained HTML regression report |

