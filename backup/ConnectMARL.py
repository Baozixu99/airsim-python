"""
square flight - Enhanced version with weather and day/night control
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
#增强版本：添加了多种天气类型（雾/雨/沙尘）和昼夜控制功能

# ========== 仿真模式开关 ==========
# True: 纯仿真模式，不需要开发板连接，自动切换天气
# False: 正常模式，需要开发板连接进行任务分配
SIMULATION_MODE = False

# ========== 昼夜控制开关 ==========
# True: 启用昼夜时间控制（可能导致光照不自然）
# False: 禁用昼夜控制，只控制天气（推荐）
ENABLE_TIME_CONTROL = False

tasknum = 5
UAVnum = 1
# require = socket.socket()
# require.connect(("10.31.36.63", 65432))


server_ip = "10.31.160.110"   # UAV1 图像接收服务器（PC地址），端口号改成了8891 8892 8893（暂时没用到），端口转发工具需一致
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

# 如果需要昼夜变化，设置 ENABLE_TIME_CONTROL = True，并使用以下场景配置：
# weather_scenarios = [
#     ["晴天白天", 0.0, 0.0, 0.0, "2024-06-15 12:00:00", "Clear day at noon"],
#     ["轻雾白天", 0.2, 0.0, 0.0, "2024-06-15 11:00:00", "Light fog in morning"],
#     ["中雾白天", 0.4, 0.0, 0.0, "2024-06-15 12:30:00", "Medium fog at noon"],
#     ["小雨白天", 0.0, 0.5, 0.0, "2024-06-15 13:00:00", "Light rain in afternoon"],
#     ["中雨白天", 0.0, 0.8, 0.0, "2024-06-15 11:30:00", "Medium rain"],
#     ["轻度沙尘白天", 0.0, 0.0, 0.3, "2024-06-15 12:00:00", "Light dust at noon"],
#     ["晴天夜晚", 0.0, 0.0, 0.0, "2024-06-15 22:00:00", "Clear night"],
#     ["雾天夜晚", 0.35, 0.0, 0.0, "2024-06-15 21:00:00", "Foggy night"],
#     ["小雨夜晚", 0.0, 0.6, 0.0, "2024-06-15 20:00:00", "Rainy night"],
#     ["沙尘夜晚", 0.0, 0.0, 0.25, "2024-06-15 23:00:00", "Dusty night"],
# ]

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
    distance = np.sqrt(np.square(uav_state.position.x_val + orig_pos[0])+np.square(uav_state.position.y_val + orig_pos[1]))
    return distance


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
    # 全局变量声明必须在函数开始处
    global UAV_task1,UAV_task2,UAV_sensor1,UAV_sensor2,UAV_finished1,UAV_finished2

    i = 0
    pic_client = airsim.MultirotorClient()
    pic_client.simEnableWeather(True)

    # 设置初始天气场景
    set_weather_and_time(pic_client, weather_scenarios[current_weather_index])

    task_change = True
    print("图像采集线程启动")
    send_msg = "011111"

    # ========== 仿真模式：不同的执行逻辑 ==========
    if SIMULATION_MODE:
        print("\n========== 仿真模式启动 ==========")
        print("自动切换天气，每30秒切换一次")
        print("不需要开发板连接")
        print("自动为UAV分配任务")
        print("====================================\n")

        # 仿真模式下自动设置传感器类型
        UAV_sensor1 = 0  # Scene（可见光）
        UAV_sensor2 = 0

        weather_switch_timer = 0  # 天气切换计时器
        weather_interval = 30  # 每30秒切换一次天气
        task_index = 0  # 任务索引

        # 等待几秒让UAV起飞
        time.sleep(5)

        # 仿真模式下自动分配初始任务
        UAV_task1 = 0
        UAV_task2 = 1
        print(f"[仿真模式] 自动分配任务: UAV1->任务{UAV_task1+1}, UAV2->任务{UAV_task2+1}")

        while True:
            weather_switch_timer += 1

            # 定时自动切换天气
            if weather_switch_timer >= weather_interval:
                current_scenario = cycle_to_next_weather(pic_client)
                weather_switch_timer = 0
                print(f"[仿真模式] 已自动切换到下一个天气场景\n")

            # 检查UAV是否完成任务，自动分配新任务
            if UAV_finished1:
                task_index = (task_index + 1) % tasknum
                UAV_task1 = task_index
                UAV_finished1 = False
                print(f"[仿真模式] UAV1完成任务，分配新任务{UAV_task1+1}")

            if UAV_finished2:
                task_index = (task_index + 1) % tasknum
                UAV_task2 = task_index
                UAV_finished2 = False
                print(f"[仿真模式] UAV2完成任务，分配新任务{UAV_task2+1}")

            # 图像采集和本地保存
            imagetype = []
            imagetype.append(UAV_sensor1)
            imagetype.append(UAV_sensor2)
            for j in range(1,UAVnum+1):
                responses = pic_client.simGetImages([
                    airsim.ImageRequest("bottom_center", imagetype[j-1], pixels_as_float=False, compress=True)],
                    vehicle_name="UAV"+str(j))
                image_data = responses[0].image_data_uint8

                # 仅本地保存图像（不发送到远程服务器）
                try:
                    file1 = open("images/" + "UAV"+str(j) + "/" + "bottom.png", 'wb')
                    file1.write(responses[0].image_data_uint8)
                    file1.close()
                    file1 = open("images/" + "UAV" + str(j) + "/" + "bottom.txt", 'wb')
                    file1.write(str(get_uav_distance(pic_client,"UAV"+str(j))).encode())
                    file1.close()
                    print(f"[仿真模式] UAV{j} 图像已保存到本地 (剩余 {weather_interval - weather_switch_timer}秒切换天气)")
                except Exception as e:
                    print(f"[仿真模式] 保存图像失败: {e}")

            i += 1
            time.sleep(1)  # 仿真模式下每秒采集一次图像

    # ========== 开发板模式：需要开发板连接 ==========
    else:
        weather_switch_timer = 0  # 天气切换计时器
        weather_interval = 30  # 每30秒切换一次天气
        last_weather_time = time.time()  # 记录上次切换天气的时间

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # 绑定到指定端口
            s.bind(('0.0.0.0', 65432))
            s.listen(1)
            print("服务器已启动，等待开发板连接...")
            conn, addr = s.accept()

            while True:
                # ========== 定时自动切换天气（新增功能） ==========
                current_time = time.time()
                if current_time - last_weather_time >= weather_interval:
                    cycle_to_next_weather(pic_client)
                    last_weather_time = current_time
                    print(f"[开发板模式] 已自动切换天气场景\n")

                if task_change == True:
                    #with conn:
                    conn.sendall(send_msg.encode('UTF-8'))
                    print(f"已发送消息给客户端: {send_msg}")
                    recv_data = conn.recv(1024).decode("UTF-8")
                    print(f"从客户端收到的消息是：{recv_data}")

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

                # ========== 原始1229代码：UAV完成任务后的处理逻辑 ==========
                if UAV_finished1 and UAV_finished2:
                    task_change = True
                    # 更新send_msg（原有的任务完成标记逻辑保持不变）
                    arr = msg2arr(send_msg)
                    arr[0] = 3 - arr[0]
                    send_msg = arr2msg(arr)

                    UAV_finished1 = False
                    UAV_finished2 = False

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

# ========== 根据模式选择启动的线程 ==========
if SIMULATION_MODE:
    print("\n========== 仿真模式：启动图像采集+UAV控制线程 ==========")
    print("UAV将按照预定路线飞行，天气自动切换")
    print("====================================\n")
    # 启动图像采集线程 + UAV控制线程
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
else:
    print("\n========== 正常模式：启动所有线程 ==========\n")
    # 启动所有线程
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
