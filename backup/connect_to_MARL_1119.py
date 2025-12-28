"""
square flight
"""
import json
from threading import Thread
import numpy as np
import airsim
import time
import socket
import os

#科为演示使用，send_port = server_port_th1改为了send_port = server_port_th2，只发送给rk3588,因为rk3588只接收8892端口的图片（因为修改了TR_test的端口，只接受8892），8891端口留给nxp开发板使用
#该文件适用于一个开发板的情况，想仿真环境的图片都通过8892端口发送给开发板，开发板上的IR_test.py文件中uav_configs应只保留8892端口,如下：
# 例如：uav_configs = [
#     (8892, "/home/jupyterWorkspace/is2ros_yolov5_inference_zc/labels_and_dataset/dataset/my_data/", "uav2"),
# ]


tasknum = 5
UAVnum = 1
# require = socket.socket()
# require.connect(("10.31.36.63", 65432))


server_ip = "10.31.32.91"   # UAV1 图像接收服务器（PC地址），端口号改成了8891 8892 8893（暂时没用到），端口转发工具需一致
server_port_th2 = 8892


UAV_task1 = -1
UAV_task2 = -1
UAV_sensor1 = 0
UAV_sensor2 = 0
UAV_finished1 = False
UAV_finished2 = False
not_all_finished = True
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
        global UAV_finished1,UAV_finished2
        for i in range(0,point_num):
            client.moveToPositionAsync(self.points[i].point_x, self.points[i].point_y, -self.points[i].point_z-100,5, vehicle_name=UAV).join()
            print(UAV+str(i))
        if UAV == "UAV1":
            UAV_finished1 = True
            print(UAV_finished1)
        if UAV == "UAV2":
            UAV_finished2 = True
            print(UAV_finished2)


def get_uav_distance(client, name,):
    orig_pos = np.array([0., 0.])
    uav_state = client.getMultirotorState(vehicle_name=name).kinematics_estimated
    # pos = np.array([[uav_state.position.x_val + orig_pos[num, 0]],
    #                 [uav_state.position.y_val + orig_pos[num, 1]],
    #                 [uav_state.position.z_val + orig_pos[num, 2]]])
    distance = np.sqrt(np.square(uav_state.position.x_val + orig_pos[0])+np.square(uav_state.position.y_val + orig_pos[1]))
    return distance






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


                # 此处可以添加其他通信逻辑
def th1():
    client = airsim.MultirotorClient()
    client.enableApiControl(True,vehicle_name="UAV1")  # get control
    client.armDisarm(True)  # unlock
    client.takeoffAsync(vehicle_name="UAV1").join()  # takeoff
    client.moveToZAsync(-30, 2, vehicle_name="UAV1").join()  # 上升到3m高度
    k = 0
    while True:
        global UAV_task1
        if UAV_task1 == -1:
            # print("UAV1等待命令")
            continue
        print("UAV1执行任务"+str(UAV_task1+1))
        tasks[UAV_task1].do_task("UAV1",client)
        tasks[UAV_task1].do_task("UAV3", client)
        UAV_task1 = -1



def th2():
    client = airsim.MultirotorClient()
    client.enableApiControl(True, vehicle_name="UAV2")  # get control
    client.armDisarm(True,vehicle_name="UAV2")  # unlock
    client.takeoffAsync(vehicle_name="UAV2").join()  # takeoff
    client.moveToZAsync(-30, 2, vehicle_name="UAV2").join()  # 上升到3m高度
    while True:
        global UAV_task2
        if UAV_task2 == -1:
            # print("UAV2等待命令")
            continue
        print("UAV2执行任务" + str(UAV_task2+1))
        tasks[UAV_task2].do_task("UAV2", client)
        UAV_task2 = -1
def th3():
    client = airsim.MultirotorClient()
    client.enableApiControl(True, vehicle_name="UAV3")  # get control
    client.armDisarm(True, vehicle_name="UAV3")  # unlock
    client.takeoffAsync(vehicle_name="UAV3").join()  # takeoff
    client.moveToZAsync(-30, 2, vehicle_name="UAV3").join()  # 上升到3m高度
    while True:
        tasks[0].do_task("UAV3",client)


def th4():
    client = airsim.MultirotorClient()
    client.enableApiControl(True, vehicle_name="UAV4")  # get control
    client.armDisarm(True, vehicle_name="UAV4")  # unlock
    client.takeoffAsync(vehicle_name="UAV4").join()  # takeoff
    client.moveToZAsync(-30, 2, vehicle_name="UAV4").join()  # 上升到3m高度

    while True:
        tasks[1].do_task("UAV4",client)

def th5():
    client = airsim.MultirotorClient()
    client.enableApiControl(True, vehicle_name="UAV5")  # get control
    client.armDisarm(True, vehicle_name="UAV5")  # unlock
    client.takeoffAsync(vehicle_name="UAV5").join()  # takeoff
    client.moveToZAsync(-30, 2, vehicle_name="UAV5").join()  # 上升到3m高度
    while True:
        tasks[2].do_task("UAV5",client)

def msg2arr(msg):
    arr = []
    for i in msg:
        arr.append(int(i))
    return arr
def arr2msg(arr):
    k = ""
    for i in arr:
        k+=str(i)
    return k


import socket
import os
import time


def handle_client(conn, addr, send_msg):
    print(f"收到连接来自: {addr}")

    # 发送消息给客户端
    conn.sendall(send_msg.encode('UTF-8'))
    print(f"已发送消息给客户端: {send_msg}")

    # 接受消息
    recv_data = conn.recv(1024).decode("UTF-8")
    print(f"从客户端收到的消息是：{recv_data}")

    conn.close()




def th1_pic():
    i = 0
    pic_client = airsim.MultirotorClient()
    pic_client.simEnableWeather(True)
    task_change = True
    print("图像采集线程启动")
    send_msg = "011111"
    x = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # 绑定到指定端口
        s.bind(('0.0.0.0', 65432))
        s.listen(1)
        print("服务器已启动，等待连接...")
        conn, addr = s.accept()

        # while True:
        #     conn, addr = s.accept()
        #     with conn:
        #         conn.sendall(send_msg.encode('UTF-8'))
        #         print(f"已发送消息给客户端: {send_msg}")
        #         recv_data = conn.recv(1024).decode("UTF-8")
        #         print(f"从客户端收到的消息是：{recv_data}")
        while True:
            global UAV_task1,UAV_task2,UAV_sensor1,UAV_sensor2,UAV_finished1,UAV_finished2
            if task_change == True:
                #with conn:
                conn.sendall(send_msg.encode('UTF-8'))
                print(f"已发送消息给客户端: {send_msg}")
                recv_data = conn.recv(1024).decode("UTF-8")
                print(f"从客户端收到的消息是：{recv_data}")
                # require.send(send_msg.encode("UTF-8"))
                # # 接受消息
                # recv_data = require.recv(1024).decode("UTF-8")  # 1024是缓冲区大小，一般就填1024， recv是阻塞式
                # print(f"服务端回复的消息是：{recv_data}")

                for i,char in zip(range(0,4),recv_data):
                    if i == 0:
                        UAV_task1 = int(char)
                        arr = msg2arr(send_msg)
                        arr[UAV_task1+1] = 0
                        send_msg = arr2msg(arr)
                        print(send_msg)

                    if i == 1:
                        print("char:" + str(char))
                        UAV_sensor1 = int(char)
                        if UAV_sensor1 == 1:
                            UAV_sensor1 = 7
                        print("UAV_sensor:"+str(UAV_sensor1))
                    if i == 2:
                        UAV_task2 = int(char)
                        arr = msg2arr(send_msg)
                        arr[UAV_task2 + 1] = 0
                        send_msg = arr2msg(arr)
                        print(send_msg)

                    if i == 3:
                        print("char:"+str(char))
                        UAV_sensor2 = int(char)
                        if UAV_sensor2 == 1:
                            UAV_sensor2 = 7
                        print("UAV_sensor:"+str(UAV_sensor2))
                task_change = False
            if UAV_finished1 and UAV_finished2:
                task_change = True
                x = 0.4 -x
                pic_client.simSetWeatherParameter(airsim.WeatherParameter.Fog, x)
                arr = msg2arr(send_msg)
                arr[0] = 3 - arr[0]
                send_msg = arr2msg(arr)
                UAV_finished1 = False
                UAV_finished2 = False

            # if i>100:
            #     pic_client.simSetWeatherParameter(airsim.WeatherParameter.Fog,0.4)
            #     arr = msg2arr(send_msg)
            #     arr[0] = 3
            #     send_msg = arr2msg(arr)
            #     task_change = True

            imagetype = []
            imagetype.append(UAV_sensor1)
            imagetype.append(UAV_sensor2)
            for j in range(1,UAVnum+1):
                responses = pic_client.simGetImages([
                    airsim.ImageRequest("bottom_center", imagetype[j-1], pixels_as_float=False, compress=True)],
                    vehicle_name="UAV"+str(j))
                image_data = responses[0].image_data_uint8
                if j == 1:
                    send_port = server_port_th2
                # elif j == 2:
                #     send_port = server_port_th2
                # ========== Step 1: 发送图像到远程服务器 ==========
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                        sock.connect((server_ip, send_port))

                        # # 先发送图像大小
                        img_size = len(image_data)
                        print(f"UAV{j} Sending image size: {img_size} bytes to {send_port}")
                        sock.sendall(img_size.to_bytes(4, byteorder='big'))

                        # 再发送图像数据
                        sock.sendall(image_data)
                        #强制等待 0.5 秒，确保缓冲区数据飞到接收端,否则 socket 关闭太快，接收端会读到不完整的数据
                        time.sleep(1)
                except Exception as e:
                    print("发送图像失败:", e)

                # ========== Step 2: 本地保存图像 ==========
                file1 = open("images/" + "UAV"+str(j) + "/" + "bottom.png", 'wb')
                file1.write(responses[0].image_data_uint8)
                file1.close()
                file1 = open("images/" + "UAV" + str(j) + "/" + "bottom.txt", 'wb')
                file1.write(str(get_uav_distance(pic_client,"UAV"+str(j))).encode())
                file1.close()
            i += 1
            time.sleep(4) #每隔3秒发送一张图片


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
tasks = []
task1 = task()
task1.add_points(taskpoint9)
task1.add_points(taskpoint10)
task2 = task()
task2.add_points(taskpoint1)
task2.add_points(taskpoint2)
task2.add_points(taskpoint3)
task2.add_points(taskpoint4)
task3 = task()
task3.add_points(taskpoint5)
task3.add_points(taskpoint6)
task4 = task()
task4.add_points(taskpoint7)
task4.add_points(taskpoint8)
task5 = task()
task5.add_points(taskpoint11)
task5.add_points(taskpoint12)
tasks.append(task1)
tasks.append(task2)
tasks.append(task3)
tasks.append(task4)
tasks.append(task5)

t1 = Thread(target=th1)
t2 = Thread(target=th2)
t1_pic = Thread(target=th1_pic)
t3 = Thread(target=th3)
t4 = Thread(target=th4)
t5 = Thread(target=th5)

t1.start()
t2.start()
t1_pic.start()
t3.start()
t4.start()
t5.start()

t1.join()
t2.join()
t3.join()
t4.join()
t5.join()
t1_pic.join()

