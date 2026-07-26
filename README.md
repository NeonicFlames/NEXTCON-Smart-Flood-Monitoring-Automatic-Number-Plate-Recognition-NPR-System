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
