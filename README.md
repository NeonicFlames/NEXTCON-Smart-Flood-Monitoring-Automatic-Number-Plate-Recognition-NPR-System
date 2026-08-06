# NEXTCON - Smart Flood Monitoring & Automatic Number Plate Recognition (NPR) System

> **A Next-Generation Real-Time Environmental Surveillance & Vehicle Tracking Dashboard**

[![Next.js](https://img.shields.io/badge/Next.js-16.2-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.2-blue?style=for-the-badge&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-06B6D4?style=for-the-badge&logo=tailwindcss)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## Project Overview

**NEXTCON** is an integrated smart city dashboard designed for **real-time flood level monitoring** paired with **Automatic Number Plate Recognition (NPR / ANPR)**. By combining sensor analytics, camera telemetry, and vehicle surveillance, the system enables municipality operators, emergency response teams, and traffic management units to act swiftly during flood hazards while maintaining vehicle logs in sensitive zones.

---

## Key Features

- **Real-Time Flood & Water Level Analytics**: Live telemetry tracking with dynamic time-series charts powered by Recharts, featuring safety status threshold indicators (`SAFE`, `WARNING`, `DANGER`).
- **Automatic Number Plate Recognition (ANPR/NPR)**: Real-time license plate detection log showing detection timestamps, OCR confidence percentages, and vehicle search/filtering.
- **Live Surveillance Stream Feeds**: Embedded camera monitoring interfaces for real-time visual inspection of flood zones and road junctions.
- **Smart Emergency Alerts**: Multi-level alert dispatch system notifying operators of rapid water level rises or flagged license plate sightings.
- **Customizable System Settings**: Centralized configuration management for sensor water depth thresholds, camera IP streams, and notification preferences.
- **Sleek Dark Theme UI**: Tailored visual design built with Next.js 16 App Router, Tailwind CSS v4, and Lucide React icons.

---

## Repository Structure

```
flood-npr-system/
├── app/
│   ├── Alerts/           # Alert logs & notification panel
│   │   └── page.tsx
│   ├── Flood/            # Detailed flood telemetry & charts
│   │   └── page.tsx
│   ├── Settings/         # Sensor thresholds & system preferences
│   │   └── page.tsx
│   ├── Vehicles/         # ANPR license plate log & analytics
│   │   └── page.tsx
│   ├── globals.css       # Tailwind CSS & global design system
│   ├── layout.tsx        # App layout wrapper & navigation
│   └── page.tsx          # Main dashboard overview page
├── components/
│   ├── Header.tsx        # Top status bar header
│   ├── Sidebar.tsx       # Primary navigation bar
│   └── WaterChart.tsx    # Recharts time-series water level graph
├── public/               # Static assets & public media
├── package.json          # Project metadata & dependencies
└── tsconfig.json         # TypeScript configuration
```

---

## Quick Start Guide

### Prerequisites

Ensure you have the following installed on your machine:
- **Node.js**: `v18.0.0` or higher
- **npm**, **yarn**, **pnpm**, or **bun**

### Installation

1. **Clone the repository:**
   ```bash
   git clone git@github.com:NeonicFlames/NEXTCON-Smart-Flood-Monitoring-Automatic-Number-Plate-Recognition-NPR-System.git
   cd NEXTCON-Smart-Flood-Monitoring-Automatic-Number-Plate-Recognition-NPR-System
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Launch the development server:**
   ```bash
   npm run dev
   ```

4. **Access the Dashboard:**
   Open your browser and navigate to `http://localhost:3000`.

---

## Tech Stack & Dependencies

- **Framework**: [Next.js 16](https://nextjs.org/) (App Router)
- **Library**: [React 19](https://react.dev/)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/)
- **Data Visualization**: [Recharts](https://recharts.org/)
- **Icons**: [Lucide React](https://lucide.dev/)

---

## Available npm Scripts

| Command | Description |
| :--- | :--- |
| `npm run dev` | Runs the app in development mode at `http://localhost:3000` |
| `npm run build` | Compiles and builds the production application |
| `npm run start` | Starts the production server |
| `npm run lint` | Runs ESLint to check for code quality and formatting issues |

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

## ANPR + Flood Monitoring Pipeline (`Codes/rtsp_anpr.py`)

A standalone Windows application that reads one RTSP camera, detects licence
plates with YOLO, recognises Malaysian plates with EasyOCR, confirms plates
over multiple frames, reads a flood sensor over serial, and pushes readings,
alerts and confirmed detections to Supabase.

The highest-priority design goal is a **smooth, current, responsive live video
window**. The camera, display, YOLO, OCR, Supabase and serial sensor never
block one another. Stale camera frames are dropped rather than displayed late.

### Requirements

- Windows
- AMD Ryzen 5 3600 (or similar)
- NVIDIA RTX 2060 (CUDA-enabled PyTorch recommended)
- One RTSP camera
- Python 3.10+

### 1. Create a Windows virtual environment

```powershell
cd Codes
python -m venv .venv
```

### 2. Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install CUDA-enabled PyTorch

Use the **official PyTorch installation selector** at
<https://pytorch.org/get-started/locally/> and choose your CUDA version. Do
**not** guess a wheel. For example (CUDA 12.1):

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 4. Install the remaining requirements

```powershell
pip install -r requirements.txt
```

### 5. Create `.env.local`

Copy `Codes/.env.local.example` to `Codes/.env.local` and fill in your
Supabase project URL and anon key:

```powershell
Copy-Item .env.local.example .env.local
```

### 6. Edit the settings at the top of `rtsp_anpr.py`

Set `RTSP_URL`, `CAMERA_ID`, `SERIAL_PORT`, thresholds and other constants in
the **Configuration** section near the top of the file.

### 7. Place `best.pt` inside `models`

The YOLO weights must be at `models/best.pt` (relative to the project root).

### 8. Run the script

```powershell
python rtsp_anpr.py
```

Press `Q` or `ESC` to exit.

### 9. Confirm that CUDA is active

On startup the log prints either `CUDA selected (RTX 2060).` or a
`CUDA not available; falling back to CPU.` warning. You can also verify from a
Python prompt:

```powershell
python -c "import torch; print(torch.cuda.is_available())"
```

### 10. Troubleshooting

- **RTSP**: Confirm the camera is reachable and the URL/credentials are
  correct. The app auto-reconnects after a disconnect.
- **CUDA**: Ensure the CUDA-enabled PyTorch wheel matches your installed CUDA
  driver. Check `nvidia-smi` for the driver CUDA version.
- **Serial**: Confirm the COM port and baud rate. If the sensor is
  unavailable the app logs a warning and continues ANPR processing.
- **Supabase**: Confirm `.env.local` credentials. If Supabase is unavailable
  the app logs errors and continues local processing.

### Tests

Run the pure-function unit tests (no camera, GPU, serial or internet needed):

```powershell
python -m pytest -q
```

