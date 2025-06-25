# Exam Hall Monitoring System

An AI-powered real-time surveillance system designed to detect and alert on rule violations in examination halls. This project utilizes an ESP32-S3 camera module for video streaming and a Python-based YOLOv3 object detection pipeline to identify suspicious activities.

> **Project completed as part of CSE461 (Intro to Robotics) in Fall 2024.**

---

## Overview

The system captures live video streams from an ESP32-S3 camera module and processes them using a Python script that employs the YOLOv3 object detection algorithm. Upon detecting any rule violations, such as unauthorized objects or behaviors, the system:

- Captures a screenshot of the incident.
- Activates a buzzer and a red LED indicator connected to the ESP32 module.

---

## Features

- **Live Video Streaming:** Real-time video feed from the ESP32-S3 camera.
- **Object Detection:** Utilizes YOLOv3 to identify potential rule violations.
- **Alert Mechanism:** Triggers auditory and visual alerts upon detection.
- **Incident Logging:** Captures and stores images of detected violations for review.

---

## Repository Structure

```
Exam-Hall-Monitoring-System/
├── CamWebServer.ino     # Arduino sketch for ESP32-S3 camera streaming
├── detector.py          # Python script for processing video stream and detection
├── readme.txt           # Original setup instructions
├── yolov3.cfg           # YOLOv3 configuration file
├── yolov3.weights       # Pre-trained YOLOv3 weights
└── coco.names           # Class labels for YOLOv3
```

---

## Getting Started

### Prerequisites

- **Hardware:**
  - ESP32-S3 camera module
  - Buzzer and red LED indicator
- **Software:**
  - Arduino IDE with ESP32 board support
  - Python 3.x
  - Required Python libraries:
    - `opencv-python`
    - `numpy`

### Setup Instructions

1. **ESP32-S3 Camera Module:**
   - Open `CamWebServer.ino` in Arduino IDE.
   - Replace `WIFI_NAME` and `WIFI_PASSWORD` with your network credentials.
   - Upload the sketch to the ESP32-S3 module.

2. **Python Environment:**
   - Ensure `yolov3.cfg`, `yolov3.weights`, and `coco.names` are in the same directory as `detector.py`.
   - Install required Python libraries:
     ```bash
     pip install opencv-python numpy
     ```

3. **Running the Detection Script:**
   - Execute `detector.py`:
     ```bash
     python detector.py
     ```

---

## How It Works

1. **Video Streaming:**
   - The ESP32-S3 module streams video over Wi-Fi.

2. **Processing & Detection:**
   - The Python script captures the video stream.
   - Each frame is analyzed using YOLOv3 to detect predefined objects or behaviors indicative of rule violations.

3. **Alert Mechanism:**
   - Upon detection:
     - A screenshot is saved.
     - The ESP32 module is signaled to activate the buzzer and illuminate the red LED.

---
