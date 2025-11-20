"""
square flight
"""
from re import match
from threading import Thread
import numpy as np
import airsim
import time

UAVnum=5


class taskpoint(object):
    def __init__(self,point_x,point_y,point_z):
        self.point_x = point_x
        self.point_y = point_y
        self.point_z = point_z

class task(object):
    def __init__(self):
        self.points = []
    def add_points(self,taskpoint):
        self.points.append(taskpoint)
    def do_task(self,UAV,client):
        point_num = len(self.points)
        for i in range(0,point_num):
            client.moveToPositionAsync(self.points[i].point_x, self.points[i].point_y, -self.points[i].point_z-100,5, vehicle_name=UAV).join()
            print(UAV+str(i))

orig_pos = np.array([[0., 0., 0.],
                     [0., 0.,0.],
                     [0., 0., 0.]])
def get_uav_distance(client, name):
    uav_state = client.getMultirotorState(vehicle_name=name).kinematics_estimated
    num = int(name[-1])-1
    distance = (uav_state.position.x_val + orig_pos[num, 0])(uav_state.position.y_val + orig_pos[num, 1])+"#"+str(uav_state.position.z_val + orig_pos[num, 2])
    return distance


origin_point_x = -1783.749375
origin_point_y = 301.57859375
origin_point_z =  -338.6909375
taskpoint1 = taskpoint(-2234.8-origin_point_x,505.4-origin_point_y,-329.3-origin_point_z)
taskpoint2 = taskpoint(-2408.4-origin_point_x,505.4-origin_point_y,-320.6-origin_point_z)
taskpoint3 = taskpoint(-2400.5-origin_point_x,433-origin_point_y,-321.10-origin_point_z)
taskpoint4 = taskpoint(-2225.6-origin_point_x,440.1-origin_point_y,-330.7-origin_point_z)
taskpoint5 = taskpoint(-2566.1-origin_point_x,383.9-origin_point_y,-310.5-origin_point_z)
taskpoint6 = taskpoint(-2648.1-origin_point_x,384.4-origin_point_y,-304.1-origin_point_z)
taskpoint7 = taskpoint(-2679.5-origin_point_x,581.4-origin_point_y,-295.8-origin_point_z)
taskpoint8 = taskpoint(-2979.1-origin_point_x,947.3-origin_point_y,-228.1-origin_point_z)
taskpoint9 = taskpoint(-2049.6-origin_point_x,355.9-origin_point_y,-338.4-origin_point_z)
taskpoint10 = taskpoint(-2160.2-origin_point_x,351.9-origin_point_y,-334.7-origin_point_z)
taskpoint11 = taskpoint(-2229.0637-origin_point_x,355.97582-origin_point_y,-330.89015-origin_point_z)
taskpoint12 = taskpoint(-2474.1012-origin_point_x,355.81699-origin_point_y,-317.43187-origin_point_z)



# square flight
# client.moveToZAsync(-3, 1).join()  # 上升到3m高度
# client.moveToPositionAsync(5, 0, -3, 1).join()  # 飞到（5,0）点坐标
# client.moveToPositionAsync(5, 5, -3, 1).join()  # 飞到（5,5）点坐标
# client.moveToPositionAsync(0, 5, -3, 1).join()  # 飞到（0,5）点坐标
# client.moveToPositionAsync(0, 0, -3, 1).join()  # 回到（0,0）点坐标
# client.moveToPositionAsync(-523.91, 179.91, -30, 5, vehicle_name="UAV1").join()
# client.moveToPositionAsync(-523.91, 179.91, -50, 0.00001, vehicle_name="UAV1").join()
# client.moveToPositionAsync(30, 0, -30, 1).join()  # 飞到（5,0）点坐标

    # client.landAsync(vehicle_name="UAV1").join()  # land
    # client.armDisarm(False)  # lock
    # client.enableApiControl(False)  # release control

def th1():
    client = airsim.MultirotorClient()
    client.enableApiControl(True,vehicle_name="UAV1")  # get control
    client.armDisarm(True)  # unlock
    client.takeoffAsync(vehicle_name="UAV1").join()  # takeoff
    client.moveToZAsync(-30, 2, vehicle_name="UAV1").join()  # 上升到3m高度
    task1 = task()
    task1.add_points(taskpoint9)
    task1.add_points(taskpoint10)
    while True:
        task1.do_task("UAV1",client)

def th1_pic():
    i = 1
    pic_client = airsim.MultirotorClient()
    pic_client.simEnableWeather(True)
    if i> 150:
        pic_client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0.4)
    if i > 200:
        pic_client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0)
    while i<101:

    
        for j in range(1,UAVnum):
            responses = pic_client.simGetImages([
                airsim.ImageRequest("bottom_center", 0, pixels_as_float=False, compress=True)],
                vehicle_name="UAV"+str(j))
            file1 = open("images/" + "UAV"+str(j) + "/" + "eo/" +str(i) + ".png", 'wb')
            file1.write(responses[0].image_data_uint8)
            file1.close()
            responses = pic_client.simGetImages([
                airsim.ImageRequest("bottom_center", 7, pixels_as_float=False, compress=True)],
                vehicle_name="UAV" + str(j))
            file1 = open("images/" + "UAV" + str(j) + "/" + "ir/" + str(i) + ".png", 'wb')
            file1.write(responses[0].image_data_uint8)
            file1.close()
        i += 1
        time.sleep(1)

def th2():
    client = airsim.MultirotorClient()
    client.enableApiControl(True, vehicle_name="UAV2")  # get control
    client.armDisarm(True,vehicle_name="UAV2")  # unlock
    client.takeoffAsync(vehicle_name="UAV2").join()  # takeoff
    client.moveToZAsync(-30, 2, vehicle_name="UAV2").join()  # 上升到3m高度
    task2 = task()
    task2.add_points(taskpoint1)
    task2.add_points(taskpoint2)
    task2.add_points(taskpoint3)
    task2.add_points(taskpoint4)
    while True:
        task2.do_task("UAV2",client)

# def th2_pic():
#     i=0
#     while True:
#         try:
#             responses = UAV2.pic_client.simGetImages([
#                 airsim.ImageRequest("bottom_center", 0, pixels_as_float=False, compress=False)],
#                 vehicle_name="UAV2")
#             file1 = open("images/" + "UAV2" + "/" + "bottom_zc" + str(i)+".png", 'wb')  # 为了vscode展示，以固定命名覆盖
#             file1.write(responses[0].image_data_uint8)
#             file1.close()
#             i += 1
#         except Exception:
#             continue
#         time.sleep(1)

def th3():
    client = airsim.MultirotorClient()
    client.enableApiControl(True, vehicle_name="UAV3")  # get control
    client.armDisarm(True, vehicle_name="UAV3")  # unlock
    client.takeoffAsync(vehicle_name="UAV3").join()  # takeoff
    client.moveToZAsync(-30, 2, vehicle_name="UAV3").join()  # 上升到3m高度
    task3 = task()
    task3.add_points(taskpoint5)
    task3.add_points(taskpoint6)
    while True:
        task3.do_task("UAV3",client)
# def th3_pic():
#     i=0
#     while True:
#         try:
#             responses = UAV3.pic_client.simGetImages([
#                 airsim.ImageRequest("bottom_center", 0, pixels_as_float=False, compress=True)],
#                 vehicle_name="UAV3")
#             file1 = open("images/" + "UAV3" + "/" + "bottom_zc" + str(i)+".png", 'wb')  # 为了vscode展示，以固定命名覆盖
#             file1.write(responses[0].image_data_uint8)
#             file1.close()
#             i += 1
#         except Exception:
#             continue
#         time.sleep(1)

def th4():
    client = airsim.MultirotorClient()
    client.enableApiControl(True, vehicle_name="UAV4")  # get control
    client.armDisarm(True, vehicle_name="UAV4")  # unlock
    client.takeoffAsync(vehicle_name="UAV4").join()  # takeoff
    client.moveToZAsync(-30, 2, vehicle_name="UAV4").join()  # 上升到3m高度
    task4 = task()
    task4.add_points(taskpoint7)
    task4.add_points(taskpoint8)
    while True:
        task4.do_task("UAV4",client)

def th5():
    client = airsim.MultirotorClient()
    client.enableApiControl(True, vehicle_name="UAV5")  # get control
    client.armDisarm(True, vehicle_name="UAV5")  # unlock
    client.takeoffAsync(vehicle_name="UAV5").join()  # takeoff
    client.moveToZAsync(-30, 2, vehicle_name="UAV5").join()  # 上升到3m高度
    task5 = task()
    task5.add_points(taskpoint11)
    task5.add_points(taskpoint12)
    while True:
        task5.do_task("UAV5",client)
# def th4_pic():
#     i=0
#     while True:
#         try:
#             responses = UAV4.pic_client.simGetImages([
#                 airsim.ImageRequest("bottom_center", 0, pixels_as_float=False, compress=True)],
#                 vehicle_name="UAV4")
#             file1 = open("images/" + "UAV4" + "/" + "bottom_zc"+ str(i) + ".png", 'wb')  # 为了vscode展示，以固定命名覆盖
#             file1.write(responses[0].image_data_uint8)
#             file1.close()
#             i += 1
#         except Exception:
#             continue
#         time.sleep(1)

t1 = Thread(target=th1)
t2 = Thread(target=th2)
t3 = Thread(target=th3)
t4 = Thread(target=th4)
t5 = Thread(target=th5)
t1_pic = Thread(target=th1_pic)

t1.start()
t2.start()
t3.start()
t4.start()
t5.start()
t1_pic.start()

t1.join()
t2.join()
t3.join()
t4.join()
t1_pic.join()

