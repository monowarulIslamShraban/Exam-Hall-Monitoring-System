import cv2
import urllib.request
import numpy as np
import mediapipe as mp
import time
import requests
from datetime import datetime
import math
import os

# Initialize MediaPipe
mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp_face_mesh.FaceMesh(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

# ESP32 Camera URLs
camera_url = 'http://192.168.162.85:80/capture'
violation_url = 'http://192.168.162.85:80/violation'

timeout = 5
opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
urllib.request.install_opener(opener)
cv2.namedWindow("Detector", cv2.WINDOW_AUTOSIZE)

# Tracking variables
baseline_angle = None
ROTATION_THRESHOLD = 8
VIOLATION_TIME = 1
head_rotation_start = None
violation_detected = False
last_snapshot_time = 0
SNAPSHOT_COOLDOWN = 5


def notify_violation():
    try:
        response = requests.post(violation_url, timeout=timeout)
        if response.status_code == 200:
            print("Violation notification sent successfully to ESP32.")
        else:
            print(f"Failed to notify ESP32. HTTP Status: {response.status_code}")
    except Exception as e:
        print("Error while notifying ESP32:", e)


def detect_phones(frame, net, output_layers, classes):
    height, width, _ = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    phones = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5 and classes[class_id] == "cell phone":
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                phones.append([x, y, w, h])
    return phones


def calculate_head_orientation(face_landmarks, pose_landmarks):
    if not face_landmarks or not pose_landmarks:
        return None

    left_shoulder = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    left_ear = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_EAR]
    right_ear = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_EAR]

    shoulder_vector = np.array([right_shoulder.x - left_shoulder.x, right_shoulder.y - left_shoulder.y])
    head_vector = np.array([right_ear.x - left_ear.x, right_ear.y - left_ear.y])

    shoulder_vector = shoulder_vector / np.linalg.norm(shoulder_vector)
    head_vector = head_vector / np.linalg.norm(head_vector)

    angle = np.arccos(np.clip(np.dot(shoulder_vector, head_vector), -1.0, 1.0))
    angle_deg = np.degrees(angle)

    cross_product = np.cross([shoulder_vector[0], shoulder_vector[1], 0], [head_vector[0], head_vector[1], 0])

    if cross_product[2] < 0:
        angle_deg = -angle_deg

    return angle_deg


def save_violation_snapshot(frame, violation_type):
    global last_snapshot_time
    current_time = time.time()

    if current_time - last_snapshot_time >= SNAPSHOT_COOLDOWN:
        timestamp = datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
        filename = f"violation_{violation_type}_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        last_snapshot_time = current_time
        print(f"Snapshot saved: {filename}")


def process_frame(frame, net, output_layers, classes):
    global baseline_angle, head_rotation_start, violation_detected

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mesh_results = face_mesh.process(rgb_frame)
    pose_results = pose.process(rgb_frame)

    # Phone detection
    phones = detect_phones(frame, net, output_layers, classes)
    for (x, y, w, h) in phones:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(frame, 'Phone', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        save_violation_snapshot(frame, "phone")
        notify_violation()

    if mesh_results.multi_face_landmarks and pose_results.pose_landmarks:
        current_angle = calculate_head_orientation(mesh_results.multi_face_landmarks[0], pose_results.pose_landmarks)

        if baseline_angle is None and current_angle is not None:
            baseline_angle = current_angle
            print("Baseline angle set:", baseline_angle)
            return frame

        if current_angle is not None:
            angle_diff = abs(current_angle - baseline_angle)
            face_color = (0, 255, 0)

            if angle_diff >= ROTATION_THRESHOLD:
                current_time = time.time()
                if head_rotation_start is None:
                    head_rotation_start = current_time
                elif current_time - head_rotation_start >= VIOLATION_TIME:
                    face_color = (0, 0, 255)
                    if not violation_detected:
                        save_violation_snapshot(frame, "head_rotation")
                        notify_violation()
                        violation_detected = True
            else:
                head_rotation_start = None
                violation_detected = False

            mp_drawing.draw_landmarks(
                frame,
                mesh_results.multi_face_landmarks[0],
                mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(color=face_color, thickness=1, circle_radius=1),
                connection_drawing_spec=mp_drawing.DrawingSpec(color=face_color, thickness=1))

            cv2.putText(frame, f"Rotation: {angle_diff:.1f} deg", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, face_color, 2)

    return frame


# Load YOLO
print("Loading YOLO model...")
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
print("YOLO model loaded successfully!")

retries = 0
max_retries = 5

while True:
    try:
        img_resp = urllib.request.urlopen(camera_url, timeout=timeout)
        imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
        frame = cv2.imdecode(imgnp, -1)

        if frame is not None:
            retries = 0
            processed_frame = process_frame(frame, net, output_layers, classes)
            cv2.imshow('Detection System', processed_frame)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('r'):
            baseline_angle = None
            print("Resetting baseline angle...")

    except Exception as e:
        retries += 1
        print(f"{e} has occurred. Retrying...")
        if retries >= max_retries:
            print("Maximum connection retries reached. Exiting...")
            break
        time.sleep(2)
        continue

cv2.destroyAllWindows()
