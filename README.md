# Costplus IR Report Generator

A robust, enterprise-grade Windows desktop application built to automate the generation of Installation Reports (IR) and PDFs for the Cost Plus Inc. Household Electrification Program. 

## Features
* **Automated PDF Generation:** Rapidly generate pixel-perfect A4 PDF documentation utilizing reportlab and PyMuPDF.
* **Smart Image Matching:** Employs RapidFuzz to dynamically match Excel beneficiary names to respective local image folders.
* **Excel Data Parsing:** Validates and structures datasets from Excel, ensuring data integrity via strict validations on GPS coordinates, required columns, and dates.
* **Resilient Worker Architecture:** Powered by a multi-threaded `QThread` worker supervisor, handling parallel processing, preventing UI lockups, and auto-restarting frozen PDF workers.
* **State Recovery & Persistence:** A robust SQLite database engine tracking progress and maintaining job states, allowing for seamless recovery of interrupted batches.
* **Premium UI Experience:** Designed with a modern PySide6 layout featuring fluent light/dark modes, an interactive dashboard, live queue monitoring, and built-in log consoles.

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Hanshuk/WIRPG.git
cd WIRPG
```

### 2. Set Up Python Environment
Ensure you have **Python 3.11+** installed on your Windows machine.

Create and activate a virtual environment:
```bash
python -m venv venv

# On Command Prompt:
venv\Scripts\activate.bat

# On PowerShell:
venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 💻 Running the Application

To run the application directly from source (useful for development and testing):
```bash
python main.py
```

---

## 🛠️ Building the Standalone `.exe`

You can compile the application into a standalone Windows Executable (`.exe`) that doesn't require Python to be installed on the target machine.

Run the provided build batch file:
```bash
build.bat
```
This script automates `PyInstaller` utilizing the `build.spec` configuration. The final executable will be located in the `dist/` directory.

### NSIS Installer
If you wish to create a full installation wizard (with start menu shortcuts and uninstallers), compile the `installer.nsi` script using [NSIS (Nullsoft Scriptable Install System)](https://nsis.sourceforge.io/).

---

## ⚙️ How to Use Batch Processing
1. Navigate to the **Batch Processing** panel in the app.
2. Select your Data Source (`.xlsx` or `.xls`).
3. Select your Root Images Folder.
4. Set an Output Destination for the generated PDFs.
5. Click **Start Batch** and monitor progress in real-time on the Queue Monitor or Dashboard.

---
*Made By Hanshuk Sathe*
