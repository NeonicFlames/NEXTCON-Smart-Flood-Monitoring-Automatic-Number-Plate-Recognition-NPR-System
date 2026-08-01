from ultralytics import YOLO

# Load trained model
model = YOLO("models/best.pt")

# Run detection
results = model(
    "test_images/motorcycle1.jpg",
    save=True,
    conf=0.5
)

print("Detection completed")