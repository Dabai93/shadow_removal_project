#!/usr/bin/env python

import rospy
import cv2
import os
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

class ImagePublisher:
    def __init__(self):
        rospy.init_node('image_publisher', anonymous=True)

        self.operation_mode = rospy.get_param('~OperationMode')
        self.input_path = rospy.get_param('~input_path')
        self.cam_id = rospy.get_param('~CamID')
        
        self.publisher = rospy.Publisher('/image_raw', Image, queue_size=10)
        self.bridge = CvBridge()
        self.rate = rospy.Rate(10)

    def publish_imgdata(self):
        if self.operation_mode == 'realtime':
            cap = cv2.VideoCapture(self.cam_id)
            while not rospy.is_shutdown():
                ret, frame = cap.read()
                if ret:
                    ros_img = self.bridge.cv2_to_imgmsg(frame, "bgr8")
                    self.publisher.publish(ros_img)
                self.rate.sleep()
            cap.release()
        elif self.operation_mode == 'localfile':
            for file_name in os.listdir(self.input_path):
                img_path = os.path.join(self.input_path, file_name)
                img = cv2.imread(img_path)
                if img is not None:
                    ros_img = self.bridge.cv2_to_imgmsg(img, "bgr8")
                    self.publisher.publish(ros_img)
                    rospy.sleep(1.0 / self.rate.sleep_dur.to_sec())
                if rospy.is_shutdown():
                    break

if __name__ == '__main__':
    try:
        image_publisher = ImagePublisher()
        image_publisher.publish_imgdata()
    except rospy.ROSInterruptException:
        pass