# STM32 HIL Validation Dashboard

Automated firmware validation and Hardware-in-the-Loop test framework for an STM32F407 target using Python, pytest, pyserial, CI/CD, and a Qt-based validation dashboard.

> Status: Work in progress

---

## Overview

This project builds a complete embedded firmware validation environment around a real STM32F407 target.

The objective is not only to test UART commands, but to develop a structured validation framework capable of:

- generating automated test stimuli,
- communicating with a real embedded DUT,
- comparing actual and expected behavior,
- performing functional and robustness testing,
- detecting firmware and communication failures,
- extending validation toward Hardware-in-the-Loop,
- running regression campaigns,
- generating test reports,
- and providing a dedicated Qt-based test dashboard.

---

## Current Test Coverage
Functional LED command tests
Negative command testing
Parametrized data-driven testing
Incomplete-frame testing
Fragmented-frame testing
Back-to-back command robustness testing

---

## Technologies

STM32F407, Embedded C, STM32 HAL, UART, Python, pytest, pyserial, Git, GitHub

---

## Roadmap
UART DMA / continuous reception
Boundary and overflow testing
Fault injection
Automated reporting
Hardware-level validation
HIL
CI/CD
Qt/PySide6 dashboard

---

##Status

Work in progress
