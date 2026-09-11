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

The project follows a test-engineering workflow:

```text
Requirement
    ↓
Test Case
    ↓
Stimulus Generation
    ↓
STM32 DUT
    ↓
Response / Hardware Observation
    ↓
Expected vs Actual
    ↓
PASS / FAIL
    ↓
Logging / Reporting
