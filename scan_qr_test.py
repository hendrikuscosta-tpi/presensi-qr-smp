import cv2
from pyzbar import pyzbar

# Buka webcam (0 = webcam utama)
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)


if not cap.isOpened():
    print("❌ Webcam tidak bisa dibuka")
    exit()

print("✅ Webcam aktif. Arahkan QR ke kamera...")
print("Tekan Q untuk keluar")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Gagal membaca kamera")
        break

    # Baca QR dari frame
    qrcodes = pyzbar.decode(frame)

    for qr in qrcodes:
        qr_data = qr.data.decode("utf-8")
        x, y, w, h = qr.rect

        # Kotak di QR
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Tampilkan isi QR
        cv2.putText(
            frame,
            qr_data,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        print("QR TERBACA:", qr_data)

    cv2.imshow("SCAN QR - TEST", frame)

    # Tekan Q untuk keluar
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
