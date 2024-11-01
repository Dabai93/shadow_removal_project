#!/usr/bin/env python

import os
import sys
import rospy
import cv2
import torch
import time
import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
sys.path.append(os.path.dirname('/home/luni/DCShadowNet_test.py'))

try:
    from DCShadowNet_test import DCShadowNet
except ModuleNotFoundError:
    print("DCShadowNet_test.py not found. Please check the path.")
    sys.exit(1)

import threading

class ImageSubscriber:
    def __init__(self):
        rospy.init_node('image_subscriber', anonymous=True)
        
        self.mode = rospy.get_param('~OperationMode')
        self.output_path = rospy.get_param('~output_path')

        self.subscriber = rospy.Subscriber('/image_raw', Image, self.process_image)
        self.bridge = CvBridge()

        self.gan = DCShadowNet()  
        self.gan.build_model()
        self.gan.eval()

    def process_image(self, data):
        img = self.bridge.imgmsg_to_cv2(data, "bgr8")
        # 通过创建线程单独处理图像推理
        threading.Thread(target=self.imgdata_inference, args=(img,)).start()  

    def imgdata_inference(self, img):
        start_time = time.time()
        
        # 将图像转换并通过GAN处理
        with torch.no_grad():
            img_tensor = self.gan.test_transform(img).unsqueeze(0).to(self.gan.device)
            fake_img, _, _ = self.gan.genA2B(img_tensor)
            result = self.imgformat_convert(fake_img[0].cpu().numpy())

        # 根据模式选择保存或显示图像
        if self.mode == "localfile":
            cv2.imwrite(f'{self.output_path}/processed_image.jpg', result) 
        else:
            frame_rate = 1.0 / (time.time() - start_time) if start_time > 0 else 0
            result = cv2.putText(result, f'Frame Rate: {frame_rate:.2f} FPS', 
                                 (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, 
                                 (255, 0, 0), 2, cv2.LINE_AA)
            cv2.imshow('Processed Image', result)
            cv2.waitKey(1)  

    def imgformat_convert(self, img_tensor):
        img_tensor = (img_tensor * 0.5 + 0.5) * 255 
        return img_tensor.astype(np.uint8)

if __name__ == '__main__':
    try:
        
        img_subscriber = ImageSubscriber()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass