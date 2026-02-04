import cv2
from pyzbar.pyzbar import decode
import time
import requests

API_URL = "http://127.0.0.1:5000/scan_qr"
PRESENSI_ID = 1  # SESUAIKAN DENGAN SESI YANG AKTIF

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("❌ Webcam tidak bisa dibuka")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("✅ Webcam aktif")
print("Arahkan QR ke kamera")
print("Tekan Q untuk keluar")

last_qr = None
last_time = 0
COOLDOWN = 3  # detik

# WARNA STATUS
COLOR_SUCCESS = (0, 255, 0)
COLOR_DUPLICATE = (0, 255, 255)
COLOR_ERROR = (0, 0, 255)

display_message = ""
display_color = (255, 255, 255)
display_until = 0
DISPLAY_DURATION = 2  # detik

while True:
    ret, frame = cap.read()
    if not ret:
        break

    barcodes = decode(frame)

    for barcode in barcodes:
        data = barcode.data.decode("utf-8")
        now = time.time()

        # CLIENT-SIDE THROTTLE
        if data == last_qr and (now - last_time) < COOLDOWN:
            continue

        last_qr = data
        last_time = now

        print("📌 QR TERBACA:", data)

        try:
            response = requests.post(
                API_URL,
                json={
                    "kode_qr": data,
                    "presensi_id": PRESENSI_ID
                },
                timeout=3
            )
            result = response.json()

        except requests.exceptions.RequestException:
            result = {
                "status": "error",
                "message": "Server tidak terhubung"
            }

        status = result.get("status")
        message = result.get("message", "")

        if status == "success":
            display_color = COLOR_SUCCESS
        elif status == "duplicate":
            display_color = COLOR_DUPLICATE
        else:
            display_color = COLOR_ERROR
        
        display_message = message
        display_until = time.time() + DISPLAY_DURATION      

        if status == "success":
            color = COLOR_SUCCESS
        elif status == "duplicate":
            color = COLOR_DUPLICATE
        else:
            color = COLOR_ERROR

        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        cv2.putText(
            frame,
            message,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2
        )

    if time.time() < display_until:
        cv2.putText(
            frame,
            display_message,
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            display_color,
            3
        )

    cv2.imshow("Scan QR Presensi", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
