"""
square flight
"""
from threading import Thread

import airsim
import time

# connect to the AirSim simulator

def th1():
    client = airsim.MultirotorClient()
    client.enableApiControl(True,vehicle_name="UAV1")  # get control
    client.armDisarm(True)  # unlock
    client.takeoffAsync(vehicle_name="UAV1").join()  # takeoff

# square flight
# client.moveToZAsync(-3, 1).join()  # 上升到3m高度
    while True:
        client.moveToPositionAsync(5, 0, -3, 1,vehicle_name="UAV1").join()  # 飞到（5,0）点坐标
        client.moveToPositionAsync(5, 5, -3, 1,vehicle_name="UAV1").join()  # 飞到（5,5）点坐标
        client.moveToPositionAsync(0, 5, -3, 1,vehicle_name="UAV1").join()  # 飞到（0,5）点坐标
        client.moveToPositionAsync(0, 0, -3, 1,vehicle_name="UAV1").join()  # 回到（0,0）点坐标
    # client.moveToZAsync(-30, 1,vehicle_name="UAV2").join()  # 上升到3m高度
    # client.moveToPositionAsync(-523.91, 179.91, -30, 5, vehicle_name="UAV2").join()
    # client.moveToPositionAsync(-523.91, 179.91, -50, 0.00001, vehicle_name="UAV2").join()
# client.moveToPositionAsync(30, 0, -30, 1).join()  # 飞到（5,0）点坐标

        client.landAsync().join()  # land
        client.armDisarm(False)  # lock
        client.enableApiControl(False)  # release control

def th2():
    client = airsim.MultirotorClient()
    client.enableApiControl(True, vehicle_name="UAV2")  # get control
    client.armDisarm(True)  # unlock
    client.takeoffAsync().join()  # takeoff

    # square flight
    # client.moveToZAsync(-3, 1).join()  # 上升到3m高度
    while True:
        client.moveToPositionAsync(5, 0, -10, 1, vehicle_name="UAV2").join()  # 飞到（5,0）点坐标
        client.moveToPositionAsync(5, 5, -10, 1, vehicle_name="UAV2").join()  # 飞到（5,5）点坐标
        client.moveToPositionAsync(0, 5, -10, 1, vehicle_name="UAV2").join()  # 飞到（0,5）点坐标
        client.moveToPositionAsync(0, 0, -10, 1, vehicle_name="UAV2").join()  # 回到（0,0）点坐标
    # client.moveToZAsync(-30, 1,vehicle_name="UAV2").join()  # 上升到3m高度
    # client.moveToPositionAsync(-523.91, 179.91, -30, 5, vehicle_name="UAV2").join()
    # client.moveToPositionAsync(-523.91, 179.91, -50, 0.00001, vehicle_name="UAV2").join()
    # client.moveToPositionAsync(30, 0, -30, 1).join()  # 飞到（5,0）点坐标

    client.landAsync().join()  # land
    client.armDisarm(False)  # lock
    client.enableApiControl(False)  # release control

t1 = Thread(target=th1)
t2 = Thread(target=th2)

t1.start()
t2.start()

t1.join()
t2.join()