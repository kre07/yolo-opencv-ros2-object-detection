# ROS 2 YOLO Rover Perception

Real-time object detection pipeline for a rover using **ROS 2**, **Python**, **OpenCV**, and **Ultralytics YOLO**.

The detector subscribes to a USB camera image topic, runs YOLO inference, publishes `vision_msgs/Detection2DArray` messages on `/detections`, and can also publish an annotated debug image on `/debug_image`.

## Pipeline

```text
USB Camera
   ↓
/image_raw
   ↓
ROS 2 Python detector node
   ↓
OpenCV frame conversion
   ↓
YOLO11n TensorRT inference
   ↓
/detections + /debug_image
```

> This repository contains the perception side of the rover system. It publishes detections into ROS 2. Nav2 / behavior-tree consumption is not included in this repository.

## Requirements

- Ubuntu with ROS 2 installed
- Python 3
- NVIDIA Jetson / CUDA-capable NVIDIA GPU for the TensorRT engine configuration used here
- `usb_cam`
- `vision_msgs`
- OpenCV
- NumPy
- Ultralytics YOLO

Install Python dependencies:

```bash
pip install ultralytics opencv-python numpy
```

## 1. Export YOLO11n to TensorRT

```bash
yolo export model=yolo11n.pt format=engine device=0
```

This creates the `yolo11n.engine` file expected by the detector.

## 2. Build the ROS 2 package

```bash
cd ~/ros2_ws/src
git clone <YOUR_REPOSITORY_URL>
cd ~/ros2_ws
colcon build --packages-select rover_perception
source install/setup.bash
```

## 3. Start the USB camera

```bash
ros2 run usb_cam usb_cam_node_exe --ros-args \
  -p video_device:=/dev/video0 \
  -p pixel_format:=mjpeg2rgb \
  -p image_width:=640 \
  -p image_height:=480 \
  -p framerate:=30.0
```

## 4. Start the detector

```bash
cd ~/ros2_ws
source install/setup.bash
ros2 run rover_perception webcam_detector
```

## ROS 2 Topics

### Subscribed

- `/image_raw` — `sensor_msgs/msg/Image`

### Published

- `/detections` — `vision_msgs/msg/Detection2DArray`
- `/debug_image` — `sensor_msgs/msg/Image`

## Detector output

Each detection includes:

- class label
- YOLO confidence score
- bounding-box center
- bounding-box width and height

The annotated `/debug_image` stream is only produced when there is a subscriber, reducing unnecessary CPU work.

## Notes

- The detector loads `yolo11n.engine`.
- Inference uses GPU device `0` and FP16.
- Input inference size is `640`.
- The ROS subscription queue is intentionally small to reduce stale-frame processing.
