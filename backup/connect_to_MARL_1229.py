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
#测试大概测试，在飞腾派开发板以及rk3588上可运行（注：只能单个开发板）

tasknum = 5
UAVnum = 1
# require = socket.socket()
# require.connect(("10.31.36.63", 65432))


server_ip = "10.31.188.214"   # UAV1 图像接收服务器（PC地址），端口号改成了8891 8892 8893（暂时没用到），端口转发工具需一致
server_port_th2 = 8892


UAV_task1 = -1
UAV_task2 = -1
UAV_sensor1 = 0
UAV_sensor2 = 0
UAV_finished1 = False
UAV_finished2 = False
not_all_finished = True

# ========== 天气和昼夜控制变量 ==========
current_weather_index = 0  # 当前天气场景索引

# 天气场景配置列表：[场景名称, 雾浓度, 雨浓度, 沙尘浓度, 时间字符串, 描述]
# 注意：如果 ENABLE_TIME_CONTROL = False，时间字符串不会生效，所有场景都使用UE默认光照
weather_scenarios = [
    ["晴天", 0.0, 0.0, 0.0, "2024-06-15 12:00:00", "Clear weather"],
    ["轻雾", 0.2, 0.0, 0.0, "2024-06-15 11:00:00", "Light fog"],
    ["中雾", 0.4, 0.0, 0.0, "2024-06-15 12:30:00", "Medium fog"],
    ["小雨", 0.0, 0.5, 0.0, "2024-06-15 13:00:00", "Light rain"],
    ["中雨", 0.0, 0.8, 0.0, "2024-06-15 11:30:00", "Medium rain"],
    ["轻度沙尘", 0.0, 0.0, 0.3, "2024-06-15 12:00:00", "Light dust"],
    ["重雾", 0.6, 0.0, 0.0, "2024-06-15 22:00:00", "Heavy fog"],
    ["大雾", 0.5, 0.0, 0.0, "2024-06-15 21:00:00", "Dense fog"],
    ["大雨", 0.0, 0.9, 0.0, "2024-06-15 20:00:00", "Heavy rain"],
    ["中度沙尘", 0.0, 0.0, 0.4, "2024-06-15 23:00:00", "Medium dust"],
]
# 如果不需要时间控制（推荐），可以简化场景配置，忽略时间字符串
# weather_scenarios_simple = [
#     ["晴天", 0.0, 0.0, 0.0, "", "Clear weather"],
#     ["轻雾", 0.2, 0.0, 0.0, "", "Light fog"],
#     ["小雨", 0.0, 0.5, 0.0, "", "Light rain"],
#     ["轻度沙尘", 0.0, 0.0, 0.3, "", "Light dust"],
# ]

# (或者直接用简化版覆盖)
# weather_scenarios = weather_scenarios_simple

# ========== 昼夜控制开关 (固定为 False，因为我们不使用时间控制) ==========
# False: 禁用昼夜控制，只控制天气（推荐）
ENABLE_TIME_CONTROL = False # <--- 添加这个常量并设为 False
# ========== 天气和时间控制函数 ==========
def set_weather_and_time(client, scenario):
    """
    设置天气和时间
    scenario: [场景名称, 雾浓度, 雨浓度, 沙尘浓度, 时间字符串, 描述]
    """
    name, fog, rain, dust, time_str, desc = scenario

    print(f"\n========== 切换天气场景 ==========")
    print(f"场景: {name} - {desc}")
    print(f"雾: {fog}, 雨: {rain}, 沙尘: {dust}")
    if ENABLE_TIME_CONTROL:
        print(f"时间: {time_str}")
    else:
        print(f"时间控制: 已禁用（使用UE默认光照）")
    print(f"====================================\n")

    # 启用天气系统
    client.simEnableWeather(True)

    # 设置天气参数
    client.simSetWeatherParameter(airsim.WeatherParameter.Fog, fog)
    client.simSetWeatherParameter(airsim.WeatherParameter.Rain, rain)
    client.simSetWeatherParameter(airsim.WeatherParameter.Dust, dust)

    # 根据开关决定是否设置时间
    if ENABLE_TIME_CONTROL:
        try:
            client.simSetTimeOfDay(
                is_enabled=True,
                start_datetime=time_str,
                is_start_datetime_dst=False,
                celestial_clock_speed=1,  # 时间流速倍数，1表示正常速度
                update_interval_secs=60,   # 更新间隔
                move_sun=True              # 移动太阳位置
            )
            print(f"时间设置成功: {time_str}")
        except Exception as e:
            print(f"时间设置失败（可能需要UE场景配置Movable光源）: {e}")
    else:
        # 禁用时间控制，使用UE场景的默认光照
        try:
            client.simSetTimeOfDay(is_enabled=False)
        except:
            pass  # 如果API不支持，忽略错误


def cycle_to_next_weather(client):
    """
    循环到下一个天气场景
    """
    global current_weather_index
    current_weather_index = (current_weather_index + 1) % len(weather_scenarios)
    set_weather_and_time(client, weather_scenarios[current_weather_index])
    return weather_scenarios[current_weather_index]

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
    # 需要在函数开头声明全局变量
    global UAV_task1, UAV_task2, UAV_sensor1, UAV_sensor2, UAV_finished1, UAV_finished2, current_weather_index

    i = 0
    pic_client = airsim.MultirotorClient()
    print("图像采集线程启动")
    task_change = True

    # 定义天气类型与消息映射
    # 可见光天气（晴天、小雨、中雨、轻度沙尘）-> "011111"
    # 红外天气（轻雾、中雾、重雾、大雾、大雨、中度沙尘）-> "311111"
    VISIBLE_LIGHT_WEATHERS = [0, 3, 4, 5]  # 对应weather_scenarios中的索引
    INFRARED_WEATHERS = [1, 2, 6, 7, 8, 9]  # 对应weather_scenarios中的索引

    # 初始化send_msg
    if current_weather_index in VISIBLE_LIGHT_WEATHERS:
        send_msg = "011111"
    else:
        send_msg = "311111"

    # 设置初始天气场景
    set_weather_and_time(pic_client, weather_scenarios[current_weather_index])
    print(f"初始天气场景: {weather_scenarios[current_weather_index][0]}, 使用消息: {send_msg}")

    weather_switch_timer = 0  # 天气切换计时器
    weather_interval = 4  # 每4次循环切换一次天气

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # 绑定到指定端口
        s.bind(('0.0.0.0', 65432))
        s.listen(1)
        print("服务器已启动，等待连接...")
        conn, addr = s.accept()

        while True:
            # ========== 新增：定时自动切换天气 ==========
            weather_switch_timer += 1
            if weather_switch_timer >= weather_interval:
                # 保存旧的天气索引
                old_weather_index = current_weather_index

                # 切换到下一个天气
                cycle_to_next_weather(pic_client)

                # 检查天气是否已切换
                if old_weather_index != current_weather_index:
                    # 根据新天气更新send_msg
                    if current_weather_index in VISIBLE_LIGHT_WEATHERS:
                        send_msg = "011111"
                    else:
                        send_msg = "311111"
                    print(f"天气已切换到: {weather_scenarios[current_weather_index][0]}, 更新消息为: {send_msg}")

                weather_switch_timer = 0  # 重置计时器
                print(f"已自动切换到下一个天气场景\n")

            if task_change == True:
                conn.sendall(send_msg.encode('UTF-8'))
                print(f"已发送消息给客户端: {send_msg}")
                recv_data = conn.recv(1024).decode("UTF-8")
                print(f"从客户端收到的消息是：{recv_data}")

                for idx, char in zip(range(0, 4), recv_data):
                    if idx == 0:
                        UAV_task1 = int(char)
                        arr = msg2arr(send_msg)
                        arr[UAV_task1 + 1] = 0
                        send_msg = arr2msg(arr)
                        print(send_msg)

                    if idx == 1:
                        print("char:" + str(char))
                        UAV_sensor1 = int(char)
                        if UAV_sensor1 == 1:
                            UAV_sensor1 = 7
                        print("UAV_sensor:" + str(UAV_sensor1))

                        # 当传感器类型变化时，更新send_msg
                        if UAV_sensor1 == 7:  # 红外
                            send_msg = "3" + send_msg[1:]
                        elif UAV_sensor1 == 0:  # 可见光
                            send_msg = "0" + send_msg[1:]

                    if idx == 2:
                        UAV_task2 = int(char)
                        arr = msg2arr(send_msg)
                        arr[UAV_task2 + 1] = 0
                        send_msg = arr2msg(arr)
                        print(send_msg)

                    if idx == 3:
                        print("char:" + str(char))
                        UAV_sensor2 = int(char)
                        if UAV_sensor2 == 1:
                            UAV_sensor2 = 7
                        print("UAV_sensor:" + str(UAV_sensor2))

                        # 当传感器类型变化时，更新send_msg
                        if UAV_sensor2 == 7:  # 红外
                            send_msg = "3" + send_msg[1:]
                        elif UAV_sensor2 == 0:  # 可见光
                            send_msg = "0" + send_msg[1:]
                task_change = False

            if UAV_finished1 and UAV_finished2:
                task_change = True
                arr = msg2arr(send_msg)
                arr[0] = 3 - arr[0]
                send_msg = arr2msg(arr)
                UAV_finished1 = False
                UAV_finished2 = False

            # ... 其余图像采集和发送逻辑保持不变 ...
            imagetype = []
            # 根据send_msg的第一个字符确定传感器类型
            current_sensor_type = int(send_msg[0])
            if current_sensor_type == 0:  # 可见光
                imagetype.append(0)
            elif current_sensor_type == 3:  # 红外
                imagetype.append(7)

            # 保持UAV_sensor1和UAV_sensor2的同步
            UAV_sensor1 = imagetype[0]
            if UAVnum > 1:
                imagetype.append(UAV_sensor2)
            else:
                imagetype.append(0)

            for j in range(1, UAVnum + 1):
                responses = pic_client.simGetImages([
                    airsim.ImageRequest("bottom_center", imagetype[j - 1], pixels_as_float=False, compress=True)],
                    vehicle_name="UAV" + str(j))
                image_data = responses[0].image_data_uint8
                if j == 1:
                    send_port = server_port_th2

                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                        sock.connect((server_ip, send_port))

                        img_size = len(image_data)
                        print(f"UAV{j} Sending image size: {img_size} bytes to {send_port}")
                        sock.sendall(img_size.to_bytes(4, byteorder='big'))
                        sock.sendall(image_data)
                        time.sleep(1)
                except Exception as e:
                    print("发送图像失败:", e)

                file1 = open("images/" + "UAV" + str(j) + "/" + "bottom.png", 'wb')
                file1.write(responses[0].image_data_uint8)
                file1.close()
                file1 = open("images/" + "UAV" + str(j) + "/" + "bottom.txt", 'wb')
                file1.write(str(get_uav_distance(pic_client, "UAV" + str(j))).encode())
                file1.close()

            i += 1
            time.sleep(4)  # 每隔4秒发送一张图片


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

