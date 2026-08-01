from ultralytics import YOLO
import easyocr
import cv2
import re
import time


# -------------------------
# Variables
# -------------------------

frame_count = 0
last_plate = ""

prev_time = time.time()


# -------------------------
# Load model
# -------------------------

model = YOLO("models/best.pt")


# -------------------------
# Load OCR
# -------------------------

reader = easyocr.Reader(
    ['en'],
    gpu=True
)


# -------------------------
# Open video
# -------------------------

cap = cv2.VideoCapture(
    "videos/entrance.mp4"
)


while True:

    ret, frame = cap.read()

    if not ret:
        break


    frame_count += 1


    # -------------------------
    # YOLO Detection
    # -------------------------

    results = model(frame)


    for result in results:

        for box in result.boxes:


            confidence = float(box.conf[0])


            if confidence < 0.5:
                continue


            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )


            # Crop plate

            plate = frame[
                y1:y2,
                x1:x2
            ]


            if plate.size == 0:
                continue



            # -------------------------
            # OCR every 5 frames
            # -------------------------

            plate_text = last_plate


            if frame_count % 5 == 0:


                ocr = reader.readtext(
                    plate
                )


                if len(ocr) > 0:


                    new_text = ocr[0][1]


                    # Clean OCR result

                    cleaned_text = re.sub(
                        r'[^A-Z0-9]',
                        '',
                        new_text.upper()
                    )


                    # Accept only reasonable plates

                    if len(cleaned_text) >= 5:

                        last_plate = cleaned_text

                        plate_text = cleaned_text



            # -------------------------
            # Draw bounding box
            # -------------------------

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0,255,0),
                2
            )


            # -------------------------
            # Display plate number
            # -------------------------

            if plate_text != "":

                cv2.putText(
                    frame,
                    plate_text,
                    (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0,255,0),
                    2
                )



    # -------------------------
    # FPS calculation
    # -------------------------

    current_time = time.time()

    fps = 1 / (current_time - prev_time)

    prev_time = current_time


    cv2.putText(
        frame,
        f"FPS: {int(fps)}",
        (20,40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0,255,0),
        2
    )


    # Show video

    cv2.imshow(
        "License Plate Detection",
        frame
    )


    if cv2.waitKey(1) == ord('q'):
        break



cap.release()

cv2.destroyAllWindows()