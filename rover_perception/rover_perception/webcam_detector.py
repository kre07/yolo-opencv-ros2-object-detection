import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
import numpy as np
import cv2
from ultralytics import YOLO
import time

class WebcamDetection2D(Node):
    def __init__(self):
        super().__init__("webcam_detector")

        # 1. Load the TensorRT Engine (Crucial for Jetson)
        # Make sure you exported yolo11n.pt to yolo11n.engine first!
        self.model = YOLO("yolo11n.engine", task="detect")
        self.get_logger().info("YOLOv11n TensorRT engine loaded")

        self.subscription = self.create_subscription(
            Image,
            "/image_raw",
            self.image_callback,
            1  # Reduced queue size to avoid processing 'old' frames
        )

        self.pub_det = self.create_publisher(Detection2DArray, "/detections", 10)
        self.pub_debug = self.create_publisher(Image, "/debug_image", 10)

        self._fps_start = time.time()
        self._fps_count = 0

    def image_msg_to_bgr(self, msg):
        # Optimized conversion
        frame = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, -1)
        if msg.encoding == 'rgb8':
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame

    def image_callback(self, msg: Image):
        frame = self.image_msg_to_bgr(msg)
        if frame is None:
            return

        # 2. Inference with FP16 (half=True) and GPU (device=0)
        # Using persist=True helps the model keep track of objects across frames
        results = self.model.predict(
            source=frame, 
            device=0, 
            half=True, 
            verbose=False, 
            imgsz=640 # Ensure this matches your export size
        )

        det_array = Detection2DArray()
        det_array.header = msg.header
        
        # We process the results directly on the GPU as much as possible
        res = results[0]
        boxes = res.boxes.cpu().numpy() # Move to CPU only when necessary

        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].astype(int)
            conf = box.conf[0]
            cls = int(box.cls[0])
            label = self.model.names[cls]

            # Simplified ROS2 message population
            detection = Detection2D()
            detection.bbox.center.position.x = float((x1 + x2) / 2)
            detection.bbox.center.position.y = float((y1 + y2) / 2)
            detection.bbox.size_x = float(x2 - x1)
            detection.bbox.size_y = float(y2 - y1)

            hypo = ObjectHypothesisWithPose()
            hypo.hypothesis.class_id = label
            hypo.hypothesis.score = float(conf)
            detection.results.append(hypo)
            det_array.detections.append(detection)

            # Draw only if there's a subscriber to save CPU
            if self.pub_debug.get_subscription_count() > 0:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        self.pub_det.publish(det_array)

        if self.pub_debug.get_subscription_count() > 0:
            debug_msg = Image()
            debug_msg.header = msg.header
            debug_msg.height, debug_msg.width = frame.shape[:2]
            debug_msg.encoding = "bgr8"
            debug_msg.step = debug_msg.width * 3
            debug_msg.data = frame.tobytes()
            self.pub_debug.publish(debug_msg)

        # FPS Calculation
        self._fps_count += 1
        now = time.time()
        if now - self._fps_start >= 1.0:
            self.get_logger().info(f"Actual Inference FPS: {self._fps_count}")
            self._fps_count = 0
            self._fps_start = now

def main(args=None):
    rclpy.init(args=args)
    node = WebcamDetection2D()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()