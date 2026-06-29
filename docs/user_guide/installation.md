# Installation Guide

Follow this guide to set up the UrbanFlow simulator environment on your local machine.

## Prerequisites

- **Python**: Version 3.9 through 3.13. Verify your version:
  ```bash
  python --version
  ```
- **pip**: Python package installer (v22.0 or newer).
- **Active Window System**: Pygame requires a GUI display output (X11, Wayland, macOS Quartz, or Windows Desktop) to render the simulator window.

## Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-org/UrbanFlow_Group2.git
   cd UrbanFlow_Group2
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the Environment**:
   - **macOS / Linux**:
     ```bash
     source venv/bin/activate
     ```
   - **Windows (CMD)**:
     ```bash
     venv\Scripts\activate.bat
     ```
   - **Windows (PowerShell)**:
     ```bash
     venv\Scripts\Activate.ps1
     ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify Dependencies**:
   ```bash
   python -c "import pygame; import numpy; import matplotlib; print('Dependencies installed successfully!')"
   ```
