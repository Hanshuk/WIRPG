# Costplus IR Report Generator

A robust, enterprise-grade desktop application built to automate the generation of Installation Reports (IR) and PDFs for the Cost Plus Inc. Household Electrification Program. 

## Features
* **Automated PDF Generation:** Rapidly generate pixel-perfect A4 PDF documentation utilizing reportlab and PyMuPDF.
* **Smart Image Matching:** Employs RapidFuzz to dynamically match Excel beneficiary names to respective local image folders.
* **Two-Tier Pre-flight Duplicate Detection:**
  * **Data Deduplication:** Scans memory-loaded Excel records for duplicate identifiers across IAS No, Name, and System Box/Solar Panel Serial Numbers.
  * **Image Deduplication:** Prevents image reuse through strict SHA-256 (exact matches) and perceptual hashing (visually identical photos via `imagehash`).
* **Guided "Idiot-Proof" Workflow:** A strictly guided, 4-step linear UI flow that locks out subsequent execution until prerequisites are fully validated. Built with plain-language, non-technical error flags.
* **Resilient Worker Architecture:** Powered by a multi-threaded `QThread` worker supervisor handling parallel processing, preventing UI lockups, and auto-restarting frozen PDF workers.
* **State Recovery & Persistence:** A robust SQLite database engine tracking progress, logging analytical data, and maintaining job states, allowing for seamless recovery of interrupted batches.
* **Premium UI Experience:** Designed with a modern PySide6 layout featuring fluent light/dark modes, an interactive "alive" dashboard, universal non-blocking dropdown notification banners, and drag-and-drop manual processing.

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Hanshuk/WIRPG.git
cd WIRPG
```

### 2. Set Up Python Environment
Ensure you have **Python 3.9+** installed on your machine.

Create and activate a virtual environment:
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
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

### Running Unit Tests
```bash
python -m unittest discover tests
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
2. Follow the numbered, visually locked 4-step workflow:
   * **Step 1:** Select your Data Source (`.xlsx` or `.xls`).
   * **Step 2:** Select your Root Images Folder.
   * **Step 3:** Set an Output Destination for the generated PDFs.
   * **Step 4:** Click **Start Batch**.
3. Any blocked duplicates or format issues will securely trigger the plain-language notification banners, refusing to generate flawed queues.
4. Monitor "alive" progress in real-time on the Dashboard, seeing precise ETAs.

---
*Made By Hanshuk Sathe*
