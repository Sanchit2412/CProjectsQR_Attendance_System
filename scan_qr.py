import cv2
from pyzbar.pyzbar import decode

cap = cv2.VideoCapture(0)

print("Scanning QR Code...")

while True:

    success, img = cap.read()

    if not success:
        break

    qr_codes = decode(img)

    for qr in qr_codes:

        qr_data = qr.data.decode('utf-8')

        print("\nQR Detected Successfully!")
        print("Data:", qr_data)

        # Split Name and Roll Number
        if "|" in qr_data:
            name, roll_no = qr_data.split("|")

            print("Name:", name)
            print("Roll Number:", roll_no)

        # Close Camera Automatically
        cap.release()
        cv2.destroyAllWindows()

        print("\nScanner Closed Successfully")
        exit()

    cv2.imshow("QR Scanner", img)

    # Press Q to close manually
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()