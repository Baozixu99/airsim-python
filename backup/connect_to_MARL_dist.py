
import os
import threading
import numpy as np
import airsim
import time
import socket

# ================= 全局变量配置 =================
tasknum = 5                     # 任务个数
UAVnum = int(os.getenv("UAV_NUM", "5"))  # 无人机个数（单机测试可设 UAV_NUM=1）

# 添加全局锁，防止多个线程同时读写 send_msg 导致数据错乱/越界
msg_lock = threading.Lock()

sockets = []
UAV_tasks = []
UAV_sensors = []
UAV_sensor_ready = []
UAV_ports = []

# 监听Windows本机所有网卡
host = '0.0.0.0'
# WSL2中IROS监听IP（可通过环境变量覆盖）
IROS_HOST = os.getenv("IROS_HOST", "10.31.32.91")
send_msg = "011111"             # 初始观测向量

# ================= 天气场景配置 =================
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

current_weather_index = 0       # 当前天气场景索引
ENABLE_TIME_CONTROL = False     # 昼夜控制开关（推荐设为False）
WEATHER_SWITCH_INTERVAL = int(os.getenv("WEATHER_SWITCH_INTERVAL", "8"))  # 天气切换循环间隔（默认更慢）

# ================= 天气和图像传输配置 =================
# 默认红外推理服务器（可被每架无人机的独立配置覆盖）
INFRARED_SERVER_HOST = os.getenv("INFRARED_SERVER_HOST", IROS_HOST)
INFRARED_SERVER_PORT = int(os.getenv("INFRARED_SERVER_PORT", "8881"))

# 每架无人机可单独指定图像接收端：
# INFRARED_SERVER_HOST_UAV1/2/3/4/5 和 INFRARED_SERVER_PORT_UAV1/2/3/4/5
INFRARED_SERVER_ENDPOINTS = []
for _i in range(1, UAVnum + 1):
    _host = os.getenv(f"INFRARED_SERVER_HOST_UAV{_i}", INFRARED_SERVER_HOST)
    _port = int(os.getenv(f"INFRARED_SERVER_PORT_UAV{_i}", str(INFRARED_SERVER_PORT)))
    INFRARED_SERVER_ENDPOINTS.append((_host, _port))

VISIBLE_LIGHT_WEATHERS = [0, 3, 4, 5]  # 对应weather_scenarios中的索引
INFRARED_WEATHERS = [1, 2, 6, 7, 8, 9]  # 对应weather_scenarios中的索引
DEBUG_IMAGE_TX = os.getenv("DEBUG_IMAGE_TX", "0") == "1"

def ensure_output_dirs():
    base_dir = "images"
    for i in range(1, UAVnum + 1):
        os.makedirs(os.path.join(base_dir, f"UAV{i}"), exist_ok=True)

# 初始化 Socket 监听
for i in range(0, UAVnum):
    port = 9999 - i
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    sockets.append(server_socket)
    print(f"监听 {host}:{port}")
    UAV_tasks.append(-1)
    UAV_sensors.append(0)
    UAV_sensor_ready.append(False)
    UAV_ports.append(8888 + i)

# ================= 天气和图像传输函数 =================
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


def update_weather_flag_in_send_msg():
    """
    将send_msg第1位同步为天气标志：
    0 = 可见光天气，3 = 红外天气
    """
    global send_msg
    weather_flag = 0 if current_weather_index in VISIBLE_LIGHT_WEATHERS else 3
    with msg_lock:
        arr = msg2arr(send_msg)
        arr[0] = weather_flag
        send_msg = arr2msg(arr)
    return weather_flag


def notify_iros_weather_once():
    """
    天气切换后，向每个IROS端口发送一次当前send_msg。
    仅发送，不在此函数中接收回复，避免和飞行线程的收包流程冲突。
    """
    with msg_lock:
        payload = send_msg.encode("UTF-8")

    for idx in range(UAVnum):
        try:
            sockets[idx].sendto(payload, (IROS_HOST, UAV_ports[idx]))
            print(f"天气同步消息已发送: UAV{idx +1} -> {IROS_HOST}:{UAV_ports[idx]}, msg={send_msg}")
        except Exception as e:
            print(f"天气同步消息发送失败: UAV{idx +1}, err={e}")


def send_image_to_server(image_data, uav_idx, image_type="png"):
    """
    通过TCP发送图像到红外推理服务器
    image_data: 图像二进制数据
    uav_idx: 无人机编号（1-based）
    image_type: 图像类型标识 (可扩展用途)
    """
    try:
        host, port = INFRARED_SERVER_ENDPOINTS[uav_idx - 1]
        # 创建TCP连接
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.5)
            s.connect((host, port))

            # 发送图像大小（4字节）
            image_size = len(image_data)
            s.sendall(image_size.to_bytes(4, byteorder='big'))

            # 发送图像数据
            s.sendall(image_data)
            if DEBUG_IMAGE_TX:
                print(f"图像已发送: UAV{uav_idx} -> {host}:{port}, bytes={image_size}")

    except Exception as e:
        print(f"发送图像到红外服务器失败 (UAV{uav_idx} -> {host}:{port}): {e}")

# ================= 任务与航点类 =================
class taskpoint(object):
    def __init__(self, point_x, point_y, point_z):
        self.point_x = point_x
        self.point_y = point_y
        self.point_z = point_z

class task(object):
    def __init__(self):
        self.points = []

    def add_points(self, taskpoint):
        self.points.append(taskpoint)

    def do_task(self, UAV, client):
        global task_change
        point_num = len(self.points)
        for i in range(0, point_num):
            client.moveToPositionAsync(
                self.points[i].point_x,
                self.points[i].point_y,
                -self.points[i].point_z - 100,
                5,
                vehicle_name=UAV
            ).join()
            print(UAV + " 到达航点 " + str(i))
        task_change = True

# ================= 辅助函数 =================
def get_uav_distance(client, name):
    orig_pos = np.array([0., 0.])
    uav_state = client.getMultirotorState(vehicle_name=name).kinematics_estimated
    distance = np.sqrt \
        (np.square(uav_state.position.x_val + orig_pos[0]) + np.square(uav_state.position.y_val + orig_pos[1]))
    return distance

def msg2arr(msg):
    arr = []
    for i in msg:
        arr.append(int(i))
    return arr

def arr2msg(arr):
    k = ""
    for i in arr:
        k += str(i)
    return k

# ================= 无人机控制线程 =================
def th1():
    try:
        client = airsim.MultirotorClient()
        client.enableApiControl(True, vehicle_name="UAV1")
        # 修复：明确解锁 UAV1
        client.armDisarm(True, vehicle_name="UAV1")
        client.takeoffAsync(vehicle_name="UAV1").join()
        client.moveToZAsync(-30, 2, vehicle_name="UAV1").join()
        print("UAV1 等待命令")

        global UAV_tasks, send_msg, UAV_sensors, UAV_sensor_ready, UAV_ports, sockets
        while True:
            if UAV_tasks[0] == -1:
                # 修复：使用对应的 socket 发送，避免端口混乱
                sockets[0].sendto(send_msg.encode("UTF-8"), (IROS_HOST, UAV_ports[0]))

                recv_data = sockets[0].recv(1024).decode("UTF-8")
                print(f"服务端回复 UAV1 的消息是：{recv_data}")
                words = recv_data.split('#')
                UAV_tasks[0] = int(words[0])

                # 修复：加锁修改全局变量
                with msg_lock:
                    arr = msg2arr(send_msg)
                    arr[UAV_tasks[0] + 1] = 0
                    send_msg = arr2msg(arr)

                sensor_val = int(words[1]) if len(words) > 1 else -1
                if sensor_val == 0:
                    UAV_sensors[0] = 0
                    UAV_sensor_ready[0] = True
                elif sensor_val in (1, 2, 3, 7):
                    UAV_sensors[0] = 7
                    UAV_sensor_ready[0] = True
                else:
                    print(f"UAV1 收到未知传感器类型: {sensor_val}, 保持当前值 {UAV_sensors[0]}")

            print("UAV1 执行任务 " + str(UAV_tasks[0]))
            tasks[UAV_tasks[0]].do_task("UAV1", client)
            print("UAV1 完成任务 " + str(UAV_tasks[0]))
            UAV_tasks[0] = -1
    except Exception as e:
        print(f"!!! UAV1 线程异常退出: {e}")

def th2():
    try:
        client = airsim.MultirotorClient()
        client.enableApiControl(True, vehicle_name="UAV2")
        client.armDisarm(True, vehicle_name="UAV2")
        client.takeoffAsync(vehicle_name="UAV2").join()
        client.moveToZAsync(-30, 2, vehicle_name="UAV2").join()
        print("UAV2 等待命令")

        global UAV_tasks, send_msg, UAV_sensors, UAV_sensor_ready, UAV_ports, sockets
        while True:
            if UAV_tasks[1] == -1:
                sockets[1].sendto(send_msg.encode("UTF-8"), (IROS_HOST, UAV_ports[1]))
                recv_data = sockets[1].recv(1024).decode("UTF-8")
                print(f"服务端回复 UAV2 的消息是：{recv_data}")
                words = recv_data.split('#')
                UAV_tasks[1] = int(words[0])

                with msg_lock:
                    arr = msg2arr(send_msg)
                    arr[UAV_tasks[1] + 1] = 0
                    send_msg = arr2msg(arr)

                sensor_val = int(words[1]) if len(words) > 1 else -1
                if sensor_val == 0:
                    UAV_sensors[1] = 0
                    UAV_sensor_ready[1] = True
                elif sensor_val in (1, 2, 3, 7):
                    UAV_sensors[1] = 7
                    UAV_sensor_ready[1] = True
                else:
                    print(f"UAV2 收到未知传感器类型: {sensor_val}, 保持当前值 {UAV_sensors[1]}")

            print("UAV2 执行任务 " + str(UAV_tasks[1]))
            tasks[UAV_tasks[1]].do_task("UAV2", client)
            print("UAV2 完成任务 " + str(UAV_tasks[1]))
            UAV_tasks[1] = -1
    except Exception as e:
        print(f"!!! UAV2 线程异常退出: {e}")

def th3():
    try:
        client = airsim.MultirotorClient()
        client.enableApiControl(True, vehicle_name="UAV3")
        client.armDisarm(True, vehicle_name="UAV3")
        client.takeoffAsync(vehicle_name="UAV3").join()
        client.moveToZAsync(-30, 2, vehicle_name="UAV3").join()
        print("UAV3 等待命令")

        global UAV_tasks, send_msg, UAV_sensors, UAV_sensor_ready, UAV_ports, sockets
        while True:
            if UAV_tasks[2] == -1:
                sockets[2].sendto(send_msg.encode("UTF-8"), (IROS_HOST, UAV_ports[2]))
                recv_data = sockets[2].recv(1024).decode("UTF-8")
                print(f"服务端回复 UAV3 的消息是：{recv_data}")
                words = recv_data.split('#')
                UAV_tasks[2] = int(words[0])

                with msg_lock:
                    arr = msg2arr(send_msg)
                    arr[UAV_tasks[2] + 1] = 0
                    send_msg = arr2msg(arr)

                sensor_val = int(words[1]) if len(words) > 1 else -1
                if sensor_val == 0:
                    UAV_sensors[2] = 0
                    UAV_sensor_ready[2] = True
                elif sensor_val in (1, 2, 3, 7):
                    UAV_sensors[2] = 7
                    UAV_sensor_ready[2] = True
                else:
                    print(f"UAV3 收到未知传感器类型: {sensor_val}, 保持当前值 {UAV_sensors[2]}")

            print("UAV3 执行任务 " + str(UAV_tasks[2]))
            tasks[UAV_tasks[2]].do_task("UAV3", client)
            print("UAV3 完成任务 " + str(UAV_tasks[2]))
            UAV_tasks[2] = -1
    except Exception as e:
        print(f"!!! UAV3 线程异常退出: {e}")

def th4():
    try:
        client = airsim.MultirotorClient()
        client.enableApiControl(True, vehicle_name="UAV4")
        client.armDisarm(True, vehicle_name="UAV4")
        client.takeoffAsync(vehicle_name="UAV4").join()
        client.moveToZAsync(-30, 2, vehicle_name="UAV4").join()
        print("UAV4 等待命令")

        global UAV_tasks, send_msg, UAV_sensors, UAV_sensor_ready, UAV_ports, sockets
        while True:
            if UAV_tasks[3] == -1:
                sockets[3].sendto(send_msg.encode("UTF-8"), (IROS_HOST, UAV_ports[3]))
                recv_data = sockets[3].recv(1024).decode("UTF-8")
                print(f"服务端回复 UAV4 的消息是：{recv_data}")
                words = recv_data.split('#')
                UAV_tasks[3] = int(words[0])

                with msg_lock:
                    arr = msg2arr(send_msg)
                    arr[UAV_tasks[3] + 1] = 0
                    send_msg = arr2msg(arr)

                sensor_val = int(words[1]) if len(words) > 1 else -1
                if sensor_val == 0:
                    UAV_sensors[3] = 0
                    UAV_sensor_ready[3] = True
                elif sensor_val in (1, 2, 3, 7):
                    UAV_sensors[3] = 7
                    UAV_sensor_ready[3] = True
                else:
                    print(f"UAV4 收到未知传感器类型: {sensor_val}, 保持当前值 {UAV_sensors[3]}")

            print("UAV4 执行任务 " + str(UAV_tasks[3]))
            tasks[UAV_tasks[3]].do_task("UAV4", client)
            print("UAV4 完成任务 " + str(UAV_tasks[3]))
            UAV_tasks[3] = -1
    except Exception as e:
        print(f"!!! UAV4 线程异常退出: {e}")

def th5():
    try:
        client = airsim.MultirotorClient()
        client.enableApiControl(True, vehicle_name="UAV5")
        client.armDisarm(True, vehicle_name="UAV5")
        client.takeoffAsync(vehicle_name="UAV5").join()
        client.moveToZAsync(-30, 2, vehicle_name="UAV5").join()
        print("UAV5 等待命令")

        global UAV_tasks, send_msg, UAV_sensors, UAV_sensor_ready, UAV_ports, sockets
        while True:
            if UAV_tasks[4] == -1:
                sockets[4].sendto(send_msg.encode("UTF-8"), (IROS_HOST, UAV_ports[4]))
                recv_data = sockets[4].recv(1024).decode("UTF-8")
                print(f"服务端回复 UAV5 的消息是：{recv_data}")
                words = recv_data.split('#')
                UAV_tasks[4] = int(words[0])

                with msg_lock:
                    arr = msg2arr(send_msg)
                    arr[UAV_tasks[4] + 1] = 0
                    send_msg = arr2msg(arr)

                sensor_val = int(words[1]) if len(words) > 1 else -1
                if sensor_val == 0:
                    UAV_sensors[4] = 0
                    UAV_sensor_ready[4] = True
                elif sensor_val in (1, 2, 3, 7):
                    UAV_sensors[4] = 7
                    UAV_sensor_ready[4] = True
                else:
                    print(f"UAV5 收到未知传感器类型: {sensor_val}, 保持当前值 {UAV_sensors[4]}")

            print("UAV5 执行任务 " + str(UAV_tasks[4]))
            tasks[UAV_tasks[4]].do_task("UAV5", client)
            print("UAV5 完成任务 " + str(UAV_tasks[4]))
            UAV_tasks[4] = -1
    except Exception as e:
        print(f"!!! UAV5 线程异常退出: {e}")

def th1_pic():
    try:
        i = 0
        pic_client = airsim.MultirotorClient()
        print("图像采集线程启动")
        ensure_output_dirs()

        # 初始化天气场景
        global current_weather_index, UAV_sensors, UAV_sensor_ready
        set_weather_and_time(pic_client, weather_scenarios[current_weather_index])
        print(f"初始天气场景: {weather_scenarios[current_weather_index][0]}")

        weather_switch_timer = 0
        weather_interval = WEATHER_SWITCH_INTERVAL  # 默认更慢，支持环境变量调整
        sensor_wait_logged = [False for _ in range(UAVnum)]

        # 启动时按当前天气写入send_msg第1位并发送一次同步消息
        weather_flag = update_weather_flag_in_send_msg()
        print(f"初始天气标志位已更新: send_msg[0]={weather_flag}")
        notify_iros_weather_once()

        while True:
            # 定时自动切换天气，并同步send_msg第1位后向IROS发送一次
            weather_switch_timer += 1
            if weather_switch_timer >= weather_interval:
                old_weather_index = current_weather_index
                cycle_to_next_weather(pic_client)

                if old_weather_index != current_weather_index:
                    weather_flag = update_weather_flag_in_send_msg()
                    notify_iros_weather_once()
                    print(
                        f"天气已切换到: {weather_scenarios[current_weather_index][0]}, "
                        f"send_msg[0]: {weather_flag}"
                    )

                weather_switch_timer = 0

            # 遍历所有无人机采集图像
            for j in range(1, UAVnum + 1):
                if not UAV_sensor_ready[j - 1]:
                    if not sensor_wait_logged[j - 1]:
                        print(f"UAV{j} 传感器类型未从IROS初始化，暂不外发图像")
                        sensor_wait_logged[j - 1] = True
                    continue

                if sensor_wait_logged[j - 1]:
                    print(f"UAV{j} 传感器类型已就绪({UAV_sensors[j - 1]})，开始外发图像")
                    sensor_wait_logged[j - 1] = False

                responses = pic_client.simGetImages([
                    airsim.ImageRequest("bottom_center", UAV_sensors[ j -1], pixels_as_float=False, compress=True)],
                    vehicle_name="UAV" +str(j))
                uav_dir = os.path.join("images", "UAV" + str(j))

                if responses and len(responses) > 0:
                    # 保存图像到本地
                    with open(os.path.join(uav_dir, "bottom.png"), 'wb') as file1:
                        file1.write(responses[0].image_data_uint8)
                    with open(os.path.join(uav_dir, "bottom.txt"), 'wb') as file1:
                        file1.write(str(get_uav_distance(pic_client, "UAV" + str(j))).encode())

                    # 任何天气都发送；图像类型由UAV_sensors决定（0可见光，7红外）
                    try:
                        send_image_to_server(responses[0].image_data_uint8, j)
                    except Exception as e:
                        print(f"发送图像失败: {e}")

            i += 1
            time.sleep(4)  # 与集中式一致：每4秒发送一轮图像

    except Exception as e:
        print(f"!!! 图像采集线程异常退出: {e}")

# ================= 构建任务 =================
origin_point_x = -1783.749375
origin_point_y = 301.57859375
origin_point_z =  -338.6909375

taskpoint1 = taskpoint(-2234.8-origin_point_x, 505.4-origin_point_y, -329.3-origin_point_z)
taskpoint2 = taskpoint(-2408.4-origin_point_x, 505.4-origin_point_y, -320.6-origin_point_z)
taskpoint3 = taskpoint(-2400.5-origin_point_x, 433-origin_point_y, -321.10-origin_point_z)
taskpoint4 = taskpoint(-2225.6-origin_point_x, 440.1-origin_point_y, -330.7-origin_point_z)
taskpoint5 = taskpoint(-2566.1-origin_point_x, 383.9-origin_point_y, -310.5-origin_point_z)
taskpoint6 = taskpoint(-2648.1-origin_point_x, 384.4-origin_point_y, -304.1-origin_point_z)
taskpoint7 = taskpoint(-2679.5-origin_point_x, 581.4-origin_point_y, -295.8-origin_point_z)
taskpoint8 = taskpoint(-2979.1-origin_point_x, 947.3-origin_point_y, -228.1-origin_point_z)
taskpoint9 = taskpoint(-2049.6-origin_point_x, 355.9-origin_point_y, -338.4-origin_point_z)
taskpoint10 = taskpoint(-2160.2-origin_point_x, 351.9-origin_point_y, -334.7-origin_point_z)
taskpoint11 = taskpoint(-2229.0637-origin_point_x, 355.97582-origin_point_y, -330.89015-origin_point_z)
taskpoint12 = taskpoint(-2474.1012-origin_point_x, 355.81699-origin_point_y, -317.43187-origin_point_z)

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

# ================= 启动线程 =================
flight_targets = [th1, th2, th3, th4, th5]
flight_threads = []
for idx in range(min(UAVnum, len(flight_targets))):
    flight_threads.append(threading.Thread(target=flight_targets[idx]))

t1_pic = threading.Thread(target=th1_pic)

print(f"开始错峰启动无人机... (UAVnum={UAVnum})")
for idx, t in enumerate(flight_threads):
    t.start()
    if idx < len(flight_threads) - 1:
        time.sleep(1)  # 错峰启动，防止 AirSim 阻塞

print("所有飞行线程启动完毕，启动图像线程...")
t1_pic.start()

for t in flight_threads:
    t.join()

t1_pic.join()