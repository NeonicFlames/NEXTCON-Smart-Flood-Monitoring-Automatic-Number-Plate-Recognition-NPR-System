from ultralytics import YOLO
import easyocr
import cv2
import os


# -------------------------
# Load YOLO model
# -------------------------

model = YOLO("models/best.pt")


# -------------------------
# Load EasyOCR
# -------------------------

print("Loading OCR model...")

reader = easyocr.Reader(
    ['en'],
    gpu=True
)


# -------------------------
# Read Image
# -------------------------

image_path = "test_images/motorcycle1.jpg"

image = cv2.imread(image_path)


if image is None:
    print("Image not found")
    exit()


# -------------------------
# YOLO Detection
# -------------------------

results = model(image)


for result in results:

    boxes = result.boxes


    for box in boxes:

        confidence = float(box.conf[0])


        if confidence < 0.5:
            continue


        # Get coordinates

        x1, y1, x2, y2 = box.xyxy[0]

        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)


        print(
            f"Plate detected confidence: {confidence:.2f}"
        )


        # -------------------------
        # Crop license plate
        # -------------------------

        plate = image[y1:y2, x1:x2]


        cv2.imwrite(
            "ocr_test/cropped_plate2.jpg",
            plate
        )


        print("Plate cropped")


        # -------------------------
        # OCR
        # -------------------------

        result = reader.readtext(
            plate
        )


        print("\nOCR Result:")

        if len(result) == 0:
            print("No text detected")

        else:

            for detection in result:

                text = detection[1]
                ocr_conf = detection[2]


                print(
                    f"{text} ({ocr_conf:.2f})"
                )