#!/usr/bin/env python

# Copyright (C) 2014 Aldebaran Robotics
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#import ROS dependencies
import rospy
from sensor_msgs.msg import Range

#import NAO dependencies
from nao_driver import NaoNode

class SonarSensor(object):

    # default values
    # NAO sonar specs
    # see https://community.aldebaran.com/doc/1-14/family/robots/sonar_robot.html
    SONAR_FREQ = 10
    SONAR_MIN_RANGE = 0.25
    SONAR_MAX_RANGE = 2.55
    SONAR_FOV = 0.523598776

    def __init__(self, memoryKey, frameID, rosTopic):
        self.memoryKey = memoryKey
        self.rosTopic = rosTopic

        self.msg = Range()
        self.msg.header.frame_id = frameID
        self.msg.min_range = self.SONAR_MIN_RANGE
        self.msg.max_range = self.SONAR_MAX_RANGE
        self.msg.field_of_view = self.SONAR_FOV
        self.msg.radiation_type = Range.ULTRASOUND


class SonarPublisher(NaoNode):

    NAOQI_SONAR_SUB_NAME = 'ros_sonar_subsription'

    def __init__(self, sonarSensorList, param_sonar_rate="~sonar_rate", sonar_rate=40):
        NaoNode.__init__(self, "sonar_publisher")
        self.sonarRate = rospy.Rate(rospy.get_param(param_sonar_rate, sonar_rate))
        self.connectNaoQi()

        self.sonarSensorList = sonarSensorList
        self.publisherList = []
        for sonarSensor in sonarSensorList:
            self.publisherList.append(
                        rospy.Publisher(sonarSensor.rosTopic, Range, queue_size=5))

    # (re-) connect to NaoQI:
    def connectNaoQi(self):
        rospy.loginfo("Connecting to NaoQi at %s:%d", self.pip, self.pport)
        self.sonarProxy = self.get_proxy("ALSonar")
        self.memProxy = self.get_proxy("ALMemory")
        if self.sonarProxy is None or self.memProxy is None:
            #self.sonarProxy.unsubscribe(NAO_SONAR_SUB_NAME)
            exit(1)

    # do it!
    def run(self):
        # start subscriber to sonar sensor
        self.sonarProxy.subscribe(self.NAOQI_SONAR_SUB_NAME)

        while self.is_looping():
            for i in range(len(self.sonarSensorList)):
                sonar = self.sonarSensorList[i]
                sonar.msg.header.stamp = rospy.Time.now()
                # fetch values
                try:
                    sonar.msg.range = self.memProxy.getData(sonar.memoryKey)
                except RuntimeError as e:
                    print 'key not found, correct robot ?', e
                    break

                # publish messages
                self.publisherList[i].publish(sonar.msg)
                #sleep
                self.sonarRate.sleep()

        #exit sonar subscription
        self.sonarProxy.unsubscribe(self.NAOQI_SONAR_SUB_NAME)
