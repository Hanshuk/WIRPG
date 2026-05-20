# Costplus IR Report Generator - Deployment Guide

## System Requirements
- **OS:** Windows 10 (1903+) or Windows 11
- **Architecture:** x64 processor
- **Memory:** 4GB RAM minimum (8GB recommended)
- **Storage:** 500MB disk space for application + space for PDF output (~500KB per PDF)

## Installation (Installer Method)
1. Run `CostplusIRReportGenerator_Setup_1.0.0.exe`.
2. Follow the installation wizard.
3. Launch from the Start Menu or Desktop shortcut.

## Installation (Portable Method)
1. Extract `CostplusIRReportGenerator_Portable.zip` to your desired location.
2. Run `CostplusIRReportGenerator.exe` directly from the extracted folder.

## First-Run Setup
1. Open the application.
2. Navigate to **Settings**.
3. Set your preferred **Default Output Folder**.
4. Adjust the **Worker Count** based on your CPU cores (default is 4).
5. Select your preferred theme (Light/Dark).

## Batch Workflow
1. Go to the **Batch Processing** panel.
2. Select the Excel dataset using the Browse button.
3. Select the Root Images folder containing beneficiary subfolders.
4. Select the Output Folder for the generated PDFs.
5. Click **Start Batch**.
6. Monitor progress and view logs in the **System Logs** panel.

## Manual Mode
1. Go to the **Manual Mode** panel.
2. Fill out all required fields.
3. Drag and drop images into the corresponding slots.
4. Click **Generate PDF**.

## Troubleshooting
- **Application won't start:** Ensure your Windows is up to date and install MSVC Redistributables.
- **PDFs not generating:** Check if the output folder has write permissions.
- **Images not matching:** Ensure folder naming closely matches the Excel Name column.
- **Crash Recovery:** If interrupted, a prompt will appear on the next launch to resume processing.

## Uninstallation
- Use **Add/Remove Programs** in Windows Settings to uninstall if using the installer version.
- Delete the folder if using the portable version.
