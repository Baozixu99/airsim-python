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
#11.19：将图片修改为发送给两个开发板，8891端口给NXP使用，8892端口给RK3588使用，需要同时修改connect_to_MARL.py和开发板中的IR_test.py



tasknum = 5
UAVnum = 2
# require = socket.socket()
# require.connect(("10.31.36.63", 65432))


server_ip_th1 = "10.31.71.190"   # UAV1 图像接收服务器（PC地址），端口号改成了8891 8892 8893（暂时没用到），端口转发工具需一致 11.19
server_ip_th2 = "10.31.33.185"   # UAV2 图像接收服务器 11.19
server_port_th1 = 8891
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
        s.listen(2)             #11.19新增 两个链接（rk3588和NXP），增加其他无人机的时候可以增加
        print("服务器已启动，等待连接...")
        conn1, addr = s.accept()  #11.19新增
        conn2, addr = s.accept() #11.19新增
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
                conn1.sendall(send_msg.encode('UTF-8'))
                print(f"已发送消息给客户端: {send_msg}")
                recv_data_1 = conn1.recv(1024).decode("UTF-8")
                print(f"从客户端收到的消息是：{recv_data_1}")
                conn2.sendall(send_msg.encode('UTF-8'))
                recv_data_2 = conn2.recv(1024).decode("UTF-8")
                print(f"从客户端收到的消息是：{recv_data_2}")
                # require.send(send_msg.encode("UTF-8"))
                # # 接受消息
                # recv_data = require.recv(1024).decode("UTF-8")  # 1024是缓冲区大小，一般就填1024， recv是阻塞式
                # print(f"服务端回复的消息是：{recv_data}")
                # recv_data = recv_data_1 + recv_data_2
                recv_data = recv_data_1  #11.19新增，后续可以和recv_data_2进行拼接，现在只用了recv_data_1，因为recv_data_1和recv_data_2都会发送3040，可以只要recv_data_1前两个30，以及recv_data_2的后两个40，然后拼接成recv_data，现在只是暂时使用了recv_data_1（图快）
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
                    send_port = server_port_th1 #11.19新增
                    server_ip=server_ip_th1     #11.19新增
                elif j == 2:
                    send_port = server_port_th2 #11.19新增
                    server_ip = server_ip_th2   #11.19新增
                # ========== Step 1: 发送图像到远程服务器 ==========
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((server_ip, send_port))

                        # # 先发送图像大小
                        img_size = len(image_data)
                        sock.sendall(img_size.to_bytes(4, byteorder='big'))

                        # 再发送图像数据
                        sock.sendall(image_data)
                except Exception as e:
                    print("发送图像失败:", e)
                    print("ip addr:",server_ip)

                # ========== Step 2: 本地保存图像 ==========
                file1 = open("images/" + "UAV"+str(j) + "/" + "bottom.png", 'wb')
                file1.write(responses[0].image_data_uint8)
                file1.close()
                file1 = open("images/" + "UAV" + str(j) + "/" + "bottom.txt", 'wb')
                file1.write(str(get_uav_distance(pic_client,"UAV"+str(j))).encode())
                file1.close()
            i += 1
            time.sleep(1)


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

