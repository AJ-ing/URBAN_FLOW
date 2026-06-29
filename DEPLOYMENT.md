# Deployment and Launch Guide

This document describes how to deploy, configure, and launch the **UrbanFlow** adaptive traffic simulation platform from a clean repository clone.

---

## 1. System Requirements

- **Python**: Python 3.9 through 3.13 (recommended: Python 3.13).
- **Operating System**: macOS, Linux, or Windows.
- **Display**: A graphical environment is required to run the simulation (Pygame depends on an active window manager). Headless execution is supported for testing and CI/CD.

---

## 2. Installation Setup

Follow these steps to set up a clean virtual environment and install all dependencies:

### Step A: Clone the Repository
```bash
git clone <repository_url>
cd UrbanFlow_POD4_Rushil
```

### Step B: Create a Virtual Environment
```bash
# On macOS/Linux
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step C: Install Dependencies
```bash
# Install core dependencies (pygame, numpy, matplotlib)
pip install -r requirements.txt

# Install developer / CI dependencies (optional)
pip install -r requirements-dev.txt
```

---

## 3. Running the Application

### Launching the Simulator
To run the interactive simulation dashboard, launch it using the package wrapper:
```bash
python src/main.py
```

### Headless Dry-Run (CI or Remote Servers)
If you are running on a server without a display, you can run the test suite or a headless execution by setting the dummy environment variables:
```bash
export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy
python src/main.py  # Launches pygame in dummy display mode
```

---

## 4. Running Quality, Testing, and Security Suites

To verify package health and reproducibility, execute the following commands in order:

### A. Run Code Formatting & Style Checks
```bash
# Formatting
black --check .
isort --check .

# Linting
flake8 .
```

### B. Run Type Checking
```bash
mypy .
```

### C. Run Security Scans
```bash
# Scan code with Bandit
bandit -r . --exclude ./venv,./tests,./test_renderer.py -s B101,B110,B311

# Scan dependencies with Safety
safety check -r requirements.txt
```

### D. Run Test Suite with Coverage
```bash
python -m pytest --cov=. --cov-report=term-missing --cov-fail-under=90
```

---

## 5. Troubleshooting & FAQ

### 1. `pygame.error: No available video device`
- **Cause**: You are running in a terminal or SSH session without an active X11 display server or window manager.
- **Solution**:
  - Make sure you are running in a graphical desktop terminal.
  - If running headless in a CI runner or docker container, export dummy variables:
    ```bash
    export SDL_VIDEODRIVER=dummy
    export SDL_AUDIODRIVER=dummy
    ```

### 2. `AttributeError: module 'simulation' has no attribute '_reset_sim'`
- **Cause**: Legacy test helper calling internal helper method that was refactored.
- **Solution**: Verify you are running the latest codebase where the public `simulation.reset_vehicles()` is defined and used.

### 3. `ModuleNotFoundError: No module named 'src'`
- **Cause**: The wrapper `src/main.py` was executed, but the parent directory was not added to the PYTHONPATH.
- **Solution**: Execute the wrapper via `python src/main.py` from the project root. The wrapper automatically manages paths and changes directory dynamically.
