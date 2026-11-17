# STM32 HIL Validation Dashboard

# STM32 HIL Validation Dashboard

## System architecture

- **PC → STM32 DUT:** Python, pytest, and the dashboard send commands through Bluetooth COM5 at 9600 baud. The Bluetooth module is connected to STM32 USART6.
- **STM32 → PC:** command responses return through USART6 and the Bluetooth serial link on COM5.
- **GPIO observation:** the Arduino HIL observer reads the DUT GPIO states and communicates with the PC on COM7 at 115200 baud.
- **Automated validation:** pytest checks command responses and, in the HIL suite, compares them with the physical GPIO states reported by the Arduino.
- **CI/CD:** `.github/workflows/hil-ci.yml` runs on pushes to `main` on a self-hosted Windows runner. It checks out the repository, installs the test dependencies, builds with Keil, flashes with STM32CubeProgrammer, runs pytest, and uploads reports and validated firmware artifacts.

## Project structure

```text
Embedded_Test_Bench_Test/
├── .github/workflows/hil-ci.yml
├── dashboard/
│   ├── dashboard.ui
│   ├── main.py
│   └── ci_config.json
├── firmware/Embedded_Test_Bench/
├── hil/arduino_hil_observer.ino
├── reports/
├── tests/
├── tools/
│   ├── serial_connection.py
│   └── github_actions.py
├── requirements.txt
├── requirements-dashboard.txt
└── pytest.ini
```

## Hardware and serial configuration

| Link | PC port | Baud rate | Purpose |
|---|---:|---:|---|
| Bluetooth module ↔ STM32 USART6 | COM5 | 9600 | DUT commands and responses |
| Arduino HIL observer | COM7 | 115200 | GPIO state observation |

The dashboard releases the serial ports before launching a pytest campaign that needs them, then reconnects them after the campaign.

### Serial diagnostic scripts

- `tools/serial_connection.py` provides the shared serial-open retry helper used by pytest and the dashboard.
- `tools/serial_debug.py` isolates a Bluetooth-to-STM32 command/response check on COM5.
- `tools/test_dual_port.py` opens COM5 and COM7 together, sends a DUT command, then reads the Arduino GPIO observation.

### Existing test baseline

The `reports/results.xml` file included with this project snapshot contains **21 test cases: 21 passed, 0 failed, 0 errors, 0 skipped**. This is the saved baseline report in the archive; it is not a new physical-hardware test run performed after the dashboard update. The 21 cases are distributed across HIL (6), invalid commands (6), LED commands (6), and robustness (3).

## Installation

Use Python 3.13 

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dashboard.txt
```

`requirements.txt` contains the CI/test dependencies. `requirements-dashboard.txt` adds PySide6 for the graphical application.

## Launch the dashboard

From the project root:

```powershell
python -u dashboard\main.py
```

The dashboard provides:

- manual Red, Green, and All LED commands over Bluetooth COM5;
- live GPIO state from the Arduino on COM7;
- separate UART and HIL pytest campaigns;
- a full regression campaign with JUnit XML and self-contained HTML reports;
- a table and summary parsed from the most recent local JUnit XML file;
- links to open the HTML report and reports folder;
- the latest GitHub Actions run and its Build, Flash, HIL, and report-upload step states.
<img width="1366" height="728" alt="dashbaord qt" src="https://github.com/user-attachments/assets/753dfbb4-c99e-461f-9416-d11e988d9acd" />


## Test campaigns

Run from the project root when the physical bench is connected:

```powershell
python -m pytest tests/test_leds.py tests/test_invalid_commands.py tests/test_robustness.py -q
python -m pytest tests/test_hil.py -q
python -m pytest -q --html=reports/test_report.html --self-contained-html --junitxml=reports/results.xml
```

The dashboard runs these commands asynchronously, so the Qt interface remains responsive while pytest is running.

## Reports

The dashboard writes:

- `reports/dashboard_uart.xml` — UART campaign results;
- `reports/dashboard_hil.xml` — HIL campaign results;
- `reports/results.xml` — full regression JUnit report;
- `reports/test_report.html` — self-contained HTML report for the full campaign.



