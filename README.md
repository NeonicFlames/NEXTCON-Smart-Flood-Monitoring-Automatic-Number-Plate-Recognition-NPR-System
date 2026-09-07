# NEXTCON Smart Flood Monitoring & Number Plate Recognition

NEXTCON combines a Next.js dashboard with Python computer-vision and sensor code for flood monitoring and vehicle number-plate recognition. The web interface reads telemetry from Supabase, while the `Codes` directory contains camera, OCR, flood-sensor, simulation, and test code.

## What is included

### Web dashboard

The Next.js application provides pages for the dashboard, flood readings, alerts, vehicles, registration, settings, and a personal vehicle view. The home screen loads the latest flood reading, recent plate detections, and daily counts, then subscribes to Supabase changes for flood readings and detections.

The API routes include:

- `POST /api/flood-reading`: reads a depth value, loads configurable warning/danger thresholds, calculates `SAFE`, `WARNING`, or `DANGER`, and stores the reading.
- `POST /api/detect`: normalizes a plate number, checks registered vehicles, stores the detection, and can create a flood alert for a registered vehicle during a warning or danger reading.

### Vision and sensor pipeline

`Codes/rtsp_anpr.py` uses OpenCV, Ultralytics YOLO, EasyOCR, serial communication, and Supabase requests. It reads two camera views, confirms detections across frames, tracks products/plates, counts defects, and sends completed inspection data through a background queue. `simulation.py` provides a simulated inspection path, and `Codes/tests/test_anpr.py` exercises pure recognition, tracking, confirmation, and duplicate-suppression logic.

## Technology

- Next.js 16, React 19, TypeScript, Tailwind CSS, and Recharts
- Supabase for readings, detections, vehicles, settings, alerts, and realtime subscriptions
- Python, OpenCV, NumPy, Ultralytics YOLO, EasyOCR, PySerial, and Requests
- Pytest for the Python test suite

## Run the web app

```bash
npm install
npm run dev
```

Configure the Supabase environment variables expected by `lib/supabase.ts` and the API routes before using data-backed pages. Use `npm run build` for a production build and `npm run start` to serve it.

## Run the vision code

```bash
cd Codes
pip install -r requirements.txt
python rtsp_anpr.py
```

The vision path requires compatible cameras, model weights, serial hardware where configured, and Supabase settings. The repository also contains simulation input/results and a pytest configuration; large media and compiled files are intentionally excluded from this documentation evidence.

## Status and limitations

This repository contains both an active-looking dashboard and hardware-dependent prototypes. It is not a self-contained deployment: database schema/configuration, credentials, camera streams, OCR/YOLO weights, and device setup must be supplied separately. Review the API validation and authentication configuration before exposing it beyond a trusted environment.
