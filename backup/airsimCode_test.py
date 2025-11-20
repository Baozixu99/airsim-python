import socket
import time
from threading import Thread

import numpy as np
from pynput import keyboard
import airsim

# 声明全局变量，便于长按监听
current_key = None
# 声明全局默认飞行速度
default_speed = 5
# 设置响应间隔时间
default_timeout = 10
now_uav = "UAV1"
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
PORTTOSEND = 8888
PORTTOSEND2 = 8889
PORTTOREC = 9999
curFog = 0.0
curRain = 0.0
curDust = 0.0
curLight = 0.01
# server_address = ("192.168.1.7", PORTTOSEND)  # 该ip接收方 服务器的ip地址和端口号
# server_address2 = ("192.168.1.7", PORTTOSEND2)  # 该ip接收方 服务器的ip地址和端口号
server_address = ("10.31.44.87", PORTTOSEND)  # 该ip接收方 服务器的ip地址和端口号
server_address2 = ("10.31.44.87", PORTTOSEND2)  # 该ip接收方 服务器的ip地址和端口号


type1 = airsim.ImageType.Scene
type2 = airsim.ImageType.Scene
type3 = airsim.ImageType.Scene

# 无人机位置读取函数封装
orig_pos = np.array([[0., 0., 0.],
                     [112., 15., 0.],
                     [44., 0., 0.]])
def get_uav_pos(client, name):
    uav_state = client.getMultirotorState(vehicle_name=name).kinematics_estimated
    num = int(name[-1])-1
    # pos = np.array([[uav_state.position.x_val + orig_pos[num, 0]],
    #                 [uav_state.position.y_val + orig_pos[num, 1]],
    #                 [uav_state.position.z_val + orig_pos[num, 2]]])
    pos = str(uav_state.position.x_val + orig_pos[num, 0])+"#"+str(uav_state.position.y_val + orig_pos[num, 1])+"#"+str(uav_state.position.z_val + orig_pos[num, 2])
    return pos

#
def th3():
    global type1
    global type2
    global type3

    for i in range(5):
        name = "UAV" + str(i + 1)
        client.enableApiControl(True, name)  # 获取控制权
        client.armDisarm(True, name)  # 解锁（螺旋桨开始转动）
        if i != 4:  # 起飞
            client.takeoffAsync(vehicle_name=name)
        else:
            client.takeoffAsync(vehicle_name=name).join()
    for i in range(5):  # 全部都飞到同一高度层
        name = "UAV" + str(i + 1)
        if i == 4:
            client.moveByVelocityAsync(0, 0, -3.5, 10, vehicle_name=name).join()
        else:
            client.moveByVelocityAsync(0, 0, -3.5, 10, vehicle_name=name)
    # for i in range(3):  # 巡逻
    #     name = "UAV" + str(i + 1)
    #     if i == 0:
    #         client.moveByVelocityAsync(3, -21, 0, 5, vehicle_name=name).join()
    #     # if i == 1:
    #         client.moveByVelocityAsync(1, -14, 0, 5, vehicle_name=name).join()
    #     # if i == 2:
    #         client.moveByVelocityAsync(1, -14, 0, 5, vehicle_name=name).join()
    # client.moveByVelocityAsync(3, -26, 0, 5, vehicle_name="UAV1").join()
    # client.moveByVelocityAsync(1, -14, 0, 5, vehicle_name="UAV2").join()
    # client.moveByVelocityAsync(1, -14, 0, 5, vehicle_name="UAV3").join()
    client.moveToPositionAsync(14.29, -56.56, -28.01, 5, vehicle_name="UAV1")
    client.moveToPositionAsync(24.29, -60.56, -28.01, 5, vehicle_name="UAV2")
    client.moveToPositionAsync(48.29, -50.56, -28.01, 5, vehicle_name="UAV3")
    client.moveToPositionAsync(18.29, -57.56, -28.01, 5, vehicle_name="UAV4")
    client.moveToPositionAsync(36.29, -59.56, -28.01, 5, vehicle_name="UAV5").join()

    for i in range(3):  # 锁定
        name = "UAV" + str(i + 1)
        if i == 0:
            client.moveByVelocityAsync(0, 0, 1.3, 5, vehicle_name=name)
        if i == 1:
            client.moveByVelocityAsync(0, 0, 0.5, 5, vehicle_name=name)# 烟雾
        if i == 2:
            client.moveByVelocityAsync(0, 0, 1, 5, vehicle_name=name).join()

    # 手动控制需要注释掉下面的循环

    # client.simEnableWeather(True)
    # for i in range(5):
    #     if i == 0:
    #         print("雾: ")
    #         type1 =  airsim.ImageType.Infrared
    #         type2 =  airsim.ImageType.Infrared
    #         type3 =  airsim.ImageType.Infrared
    #         start = time.time()  # 获取当前时间
    #         nowtimestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
    #         print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))  # 以指定格式显示当前时间,str
    #         msg = nowtimestr + "#" + "3.0" + "#" + "0.25" + "#" + "0.0" + "#" + "0.0"
    #         client_socket.sendto(msg.encode(), server_address)  # 将msg内容发送给指定接收方
    #         client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0.25)
    #         msg = nowtimestr + "#" + get_uav_pos(client, "UAV1") + "#" + get_uav_pos(client,"UAV2") + "#" + get_uav_pos(client,"UAV3")
    #         print(msg)
    #         client_socket.sendto(msg.encode(), server_address2)  # 将msg内容发送给指定接收方
    #     if i == 1:
    #         print("雨: ")
    #         type1 =  airsim.ImageType.Scene
    #         type2 =  airsim.ImageType.Scene
    #         type3 =  airsim.ImageType.Scene
    #         client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0)
    #         time.sleep(2)
    #         start = time.time()  # 获取当前时间
    #         nowtimestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
    #         print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))  # 以指定格式显示当前时间,str
    #         msg = nowtimestr + "#" + "3.0" + "#" + "0.0" + "#" + "0.99" + "#" + "0.0"
    #         client_socket.sendto(msg.encode(), server_address)  # 将msg内容发送给指定接收方
    #         client.simSetWeatherParameter(airsim.WeatherParameter.Rain, 0.99)
    #         msg = nowtimestr + "#" + get_uav_pos(client, "UAV1") + "#" + get_uav_pos(client,"UAV2") + "#" + get_uav_pos(client,"UAV3")
    #         print(msg)
    #         client_socket.sendto(msg.encode(), server_address2)  # 将msg内容发送给指定接收方
    #     if i == 2:
    #         print("灰: ")
    #         type1 =  airsim.ImageType.Infrared
    #         type2 =  airsim.ImageType.Infrared
    #         type3 =  airsim.ImageType.Infrared
    #         client.simSetWeatherParameter(airsim.WeatherParameter.Rain, 0)
    #         time.sleep(2)
    #         start = time.time()  # 获取当前时间
    #         nowtimestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
    #         print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))  # 以指定格式显示当前时间,str
    #         msg = nowtimestr + "#" + "3.0" + "#" + "0.0" + "#" + "0.0" + "#" + "0.25"
    #         client_socket.sendto(msg.encode(), server_address)  # 将msg内容发送给指定接收方
    #         client.simSetWeatherParameter(airsim.WeatherParameter.Dust, 0.25)
    #         msg = nowtimestr + "#" + get_uav_pos(client, "UAV1") + "#" + get_uav_pos(client,"UAV2") + "#" + get_uav_pos(client,"UAV3")
    #         print(msg)
    #         client_socket.sendto(msg.encode(), server_address2)  # 将msg内容发送给指定接收方
    #     if i == 3:
    #         client.simSetWeatherParameter(airsim.WeatherParameter.Dust, 0)
    #         time.sleep(3)
    #         print("亮度: ")
    #         type1 =  airsim.ImageType.Scene
    #         type2 =  airsim.ImageType.Scene
    #         type3 =  airsim.ImageType.Scene
    #         start = time.time()  # 获取当前时间
    #         nowtimestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
    #         print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))  # 以指定格式显示当前时间,str
    #         msg = nowtimestr + "#" + "0.01" + "#" + "0.0" + "#" + "0.0" + "#" + "0.0"
    #         client_socket.sendto(msg.encode(), server_address)  # 将msg内容发送给指定接收方
    #         # client.simSetWeatherParameter(airsim.WeatherParameter.Dust, 0)
    #         msg = nowtimestr + "#" + get_uav_pos(client, "UAV1") + "#" + get_uav_pos(client,"UAV2") + "#" + get_uav_pos(client,"UAV3")
    #         print(msg)
    #         client_socket.sendto(msg.encode(), server_address2)  # 将msg内容发送给指定接收方
    #     if i == 4:
    #         print("任务结束")
    #         client.moveByVelocityAsync(-3, 26, 0, 4, vehicle_name="UAV1")
    #         client.moveByVelocityAsync(-1, 14, 0, 5, vehicle_name="UAV2")
    #         client.moveByVelocityAsync(-1, 14, 0, 5, vehicle_name="UAV3").join()
    #         for i in range(3):
    #             name = "UAV" + str(i + 1)
    #             print(name)
    #             if i != 2:  # 降落
    #                 # client.landAsync(vehicle_name=name)
    #                 client.moveByVelocityAsync(0, 0, 5, 15, vehicle_name=name)
    #             else:
    #                 client.moveByVelocityAsync(0, 0, 5, 15, vehicle_name=name).join()
    #         return
    #     timefly = 2
    #     client.moveByVelocityAsync(2, 0, 0, timefly, vehicle_name="UAV1").join()
    #     client.moveByVelocityAsync(2, 0, 0, timefly, vehicle_name="UAV2").join()
    #     client.moveByVelocityAsync(2, 0, 0, timefly, vehicle_name="UAV3").join()
    #
    #     client.moveByVelocityAsync(0, 2, 0, timefly, vehicle_name="UAV1").join()
    #     client.moveByVelocityAsync(0, 2, 0, timefly, vehicle_name="UAV2").join()
    #     client.moveByVelocityAsync(0, 2, 0, timefly, vehicle_name="UAV3").join()
    #
    #     client.moveByVelocityAsync(-2, 0, 0, timefly, vehicle_name="UAV1").join()
    #     client.moveByVelocityAsync(-2, 0, 0, timefly, vehicle_name="UAV2").join()
    #     client.moveByVelocityAsync(-2, 0, 0, timefly, vehicle_name="UAV3").join()
    #
    #     client.moveByVelocityAsync(0, -2, 0, timefly, vehicle_name="UAV1").join()
    #     client.moveByVelocityAsync(0, -2, 0, timefly, vehicle_name="UAV2").join()
    #     client.moveByVelocityAsync(0, -2, 0, timefly, vehicle_name="UAV3").join()
    #
    #     print(i)
    #     time.sleep(2)

# 键盘按下事件
def on_press(key):
    global current_key, now_uav, curFog,curRain,curLight,curDust
    try:
        if key.char == 'g':
            print("截取图像")
            # response = client.simGetImage("bottom_center", airsim.ImageType.Infrared)
            # file = open("images/IR/" + str(time.time_ns()) + ".png", 'wb')
            # file.write(response)
            response = client.simGetImage("bottom_center", airsim.ImageType.Scene,vehicle_name="UAV3")
            file = open("images/RGB/" + str(time.time_ns()) + ".png", 'wb')
            file.write(response)
            file.close()
        if key.char == 'q':
            print("任务结束")
            client.moveByVelocityAsync(-3, 26, 0, 4, vehicle_name="UAV1")
            client.moveByVelocityAsync(-1, 14, 0, 5, vehicle_name="UAV2")
            client.moveByVelocityAsync(-1, 14, 0, 5, vehicle_name="UAV3").join()
            for i in range(3):
                name = "UAV" + str(i + 1)
                if i != 2:  # 降落
                    # client.landAsync(vehicle_name=name)
                    client.moveByVelocityAsync(0, 0, 5, 15, vehicle_name=name)
                else:
                    client.moveByVelocityAsync(0, 0, 5, 15, vehicle_name=name).join()
        elif key.char == 'z':
            client.simEnableWeather(True)
            if curFog >= 1:
                curFog = 0.0
            curFog += 0.05
            print("雾: "+str(curFog))

            start = time.time()  # 获取当前时间
            nowtimestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
            print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))  # 以指定格式显示当前时间,str
            msg = nowtimestr + "#" + str(curLight)+"#"+str(curFog) +"#"+str(curRain)+"#"+str(curDust)
            client_socket.sendto(msg.encode(), server_address)  # 将msg内容发送给指定接收方

            start = time.time()  # 获取当前时间
            nowtimestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
            # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))  # 以指定格式显示当前时间,str
            msg = nowtimestr + "#" + get_uav_pos(client, "UAV1") + "#" + get_uav_pos(client,"UAV2") + "#" + get_uav_pos(client, "UAV3")
            print(msg)
            client_socket.sendto(msg.encode(), server_address2)  # 将msg内容发送给指定接收方

            client.simSetWeatherParameter(airsim.WeatherParameter.Fog, curFog)
            # time.sleep(2)
        elif key.char == 'x':
            client.simEnableWeather(True)
            if curRain >= 1:
                curRain = 0.0
            curRain += 0.1
            print("雨: " + str(curRain))

            start = time.time()  # 获取当前时间
            nowtimestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
            print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))  # 以指定格式显示当前时间,str
            msg = nowtimestr + "#" + str(curLight)+"#"+str(curFog) +"#"+str(curRain)+"#"+str(curDust)
            client_socket.sendto(msg.encode(), server_address)  # 将msg内容发送给指定接收方

            start = time.time()  # 获取当前时间
            nowtimestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
            # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))  # 以指定格式显示当前时间,str
            msg = nowtimestr + "#" + get_uav_pos(client, "UAV1") + "#" + get_uav_pos(client,"UAV2") + "#" + get_uav_pos(client,"UAV3")
            print(msg)
            client_socket.sendto(msg.encode(), server_address2)  # 将msg内容发送给指定接收方

            client.simSetWeatherParameter(airsim.WeatherParameter.Rain, curRain)
            # time.sleep(2)
        elif key.char == 'c':
            client.simEnableWeather(True)
            if curDust >= 1:
                curDust = 0.0
            curDust += 0.05
            print("灰: " + str(curDust))

            start = time.time()  # 获取当前时间
            nowtimestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
            print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))  # 以指定格式显示当前时间,str
            msg = nowtimestr + "#" + str(curLight)+"#"+str(curFog) +"#"+str(curRain)+"#"+str(curDust)
            client_socket.sendto(msg.encode(), server_address)  # 将msg内容发送给指定接收方

            start = time.time()  # 获取当前时间
            nowtimestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
            # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))  # 以指定格式显示当前时间,str
            msg = nowtimestr + "#" + get_uav_pos(client, "UAV1") + "#" + get_uav_pos(client,"UAV2") + "#" + get_uav_pos(client,"UAV3")
            print(msg)
            client_socket.sendto(msg.encode(), server_address2)  # 将msg内容发送给指定接收方

            client.simSetWeatherParameter(airsim.WeatherParameter.Dust, curDust)
            # time.sleep(2)
        elif key.char == 'v':
            print("重置所有天气")
            curFog = 0.0
            curDust = 0.0
            curLight = 0.01
            curRain = 0.0
            client.simSetWeatherParameter(airsim.WeatherParameter.Rain, curRain)
            client.simSetWeatherParameter(airsim.WeatherParameter.Fog, curFog)
            client.simSetWeatherParameter(airsim.WeatherParameter.Dust, curDust)
            client.simEnableWeather(False)
        elif key.char == 'o':
            client.simSetCameraFov('1', 0.0)
        elif key.char == 'p':
            client.simSetCameraFov('1', 89.90362548828125)
        else:
            pass
    except:
        pass
    current_key = key
    # else:
    #     pass


def th1():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

#接收数据控制传感器
def th2():
    # 创建udp套接字,
    # AF_INET表示ip地址的类型是ipv4，
    # SOCK_DGRAM表示传输的协议类型是udp
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 绑定本地信息，若不绑定，系统会自动分配
    bind_addr = ('', PORTTOREC)
    udp_socket.bind(bind_addr)  # ip和port，ip一般不用写，表示本机的任何一个ip
    client2 = airsim.MultirotorClient()

    while True:
        # 等待接收数据
        revc_data = udp_socket.recvfrom(1024)  # 1024表示本次接收的最大字节数

        # 打印接收到的数据
        print("recv_from: {0} , recv_data: {1}".format(revc_data[1], revc_data[0]))
        print("收到匹配结果，开始采集图像")
        resStr = str(revc_data[0],encoding= "utf-8")
        msgs = resStr.split(" ")
        msglen = len(msgs)
        for i in range(msglen):
            if i %2 == 0:
                imgType = int(msgs[i])
            else:
                vehicle = msgs[i]
                print(imgType)
                print(vehicle)
                if vehicle == "UAV1":
                    type1 = imgType
                elif vehicle == "UAV2":
                    type2 = imgType
                else:
                    type3 = imgType
                # responses = client2.simGetImages([
                #     airsim.ImageRequest("bottom_center", imgType, pixels_as_float=False, compress=True)],
                #     vehicle_name=vehicle)
                # file = open("images/" + vehicle + "/" + str(time.time_ns()) + ".png", 'wb')

                # file.write(response)
                # file.write(responses[0].image_data_uint8)
                # file.close()
        # imgType = int(resStr[0:1])
        # vehicle = resStr[1:]
        # print(imgType)
        # print(vehicle)
        # # response = client.simGetImage("bottom_center", imgType, vehicle)
        # responses = client.simGetImages([
        #     airsim.ImageRequest("bottom_center", imgType, pixels_as_float=False, compress=True)],vehicle_name = vehicle)
        # file = open("images/"+vehicle+"/" + str(time.time_ns()) + ".png", 'wb')
        # # file.write(response)
        # file.write(responses[0].image_data_uint8)
        # file.close()

    # 关闭套接字
    udp_socket.close()

#     图像采集线程（1s一帧）
def th4():
    i=1
    while True:
        client3 = airsim.MultirotorClient()
        for k in range(1,4):
         responses = client3.simGetImages([
            airsim.ImageRequest("bottom_center", 0, pixels_as_float=False, compress=True)],
            vehicle_name="UAV"+ str(k))
         file_eo = open("images/" + "UAV" + str(k) + "/" + "eo" +str(i) + ".png", 'wb') #为了vscode展示，以固定命名覆盖
        # file2 = open("images/" + "UAV1" + "/" + str(airsim.ImageType.Infrared) + ".png", 'wb') #为了vscode展示，以固定命名覆盖
         file_eo.write(responses[0].image_data_uint8)
        # file2.write(responses[1].image_data_uint8)
         file_eo.close()
        for k in range(1,4):
         responses = client3.simGetImages([
            airsim.ImageRequest("bottom_center", 7, pixels_as_float=False, compress=True)],
            vehicle_name="UAV"+ str(k))
         file_ir = open("images/" + "UAV" + str(k) + "/" + "ir" +str(i) + ".png", 'wb') #为了vscode展示，以固定命名覆盖
        # file2 = open("images/" + "UAV1" + "/" + str(airsim.ImageType.Infrared) + ".png", 'wb') #为了vscode展示，以固定命名覆盖
         file_ir.write(responses[0].image_data_uint8)
        # file2.write(responses[1].image_data_uint8)
         file_ir.close()
        # file2.close()
        # responses = client3.simGetImages([
        #     airsim.ImageRequest("bottom_center", type2, pixels_as_float=False, compress=True)],
        #     vehicle_name="UAV2")
        # file1 = open("images/" + "UAV2" + "/" + "bottom" + ".png", 'wb')  # 为了vscode展示，以固定命名覆盖
        # # file2 = open("images/" + "UAV2" + "/" + str(airsim.ImageType.Infrared) + ".png", 'wb')  # 为了vscode展示，以固定命名覆盖
        # file1.write(responses[0].image_data_uint8)
        # # file2.write(responses[1].image_data_uint8)
        # file1.close()
        # # file2.close()
        #
        # responses = client3.simGetImages([
        #     airsim.ImageRequest("bottom_center", type3, pixels_as_float=False, compress=True)],
        #     vehicle_name="UAV3")
        # file1 = open("images/" + "UAV3" + "/" + "bottom" + ".png", 'wb')  # 为了vscode展示，以固定命名覆盖
        # # file2 = open("images/" + "UAV3" + "/" + str(airsim.ImageType.Infrared) + ".png", 'wb')  # 为了vscode展示，以固定命名覆盖
        # file1.write(responses[0].image_data_uint8)
        # # file2.write(responses[1].image_data_uint8)
        # file1.close()
        # # file2.close()
        time.sleep(1)
def th5():
    while True:
        client4 = airsim.MultirotorClient()
        responses = client4.simGetImages([
            airsim.ImageRequest("bottom_center", 0, pixels_as_float=False, compress=True)],
            vehicle_name="UAV2")
        file1 = open("images/" + "UAV2" + "/" + "bottom2" + ".png", 'wb')  # 为了vscode展示，以固定命名覆盖
        file1.write(responses[0].image_data_uint8)
        file1.close()
        time.sleep(0.5)
def th6():
    while True:
        client5 = airsim.MultirotorClient()
        responses = client5.simGetImages([
            airsim.ImageRequest("bottom_center", 0, pixels_as_float=False, compress=True)],
            vehicle_name="UAV3")
        file1 = open("images/" + "UAV3" + "/" + "bottom3" + ".png", 'wb')  # 为了vscode展示，以固定命名覆盖
        file1.write(responses[0].image_data_uint8)
        file1.close()
        time.sleep(0.5)
def th7():
    while True:
        client6 = airsim.MultirotorClient()


if __name__ == "__main__":
    # 连接无人机，开启无人机API控制，解锁无人机，无人机起飞
    client = airsim.MultirotorClient()

    # client.reset()
    # print(client.simGetCameraInfo('1'))
    #
    # lights = client.simListSceneObjects("LightSource.*")
    # print(len(lights))
    # print(client.simGetObjectPose(lights[0]))

    # 不相关的东西不显示二进制
    # print(client.simGetSegmentationObjectID('SM_PineTree_173'))
    print(client.simSetSegmentationObjectID("BP_scarp[\w]*", -1, True))
    print(client.simSetSegmentationObjectID("BP_beech[\w]*", -1, True))
    print(client.simSetSegmentationObjectID("BP_stones[\w]*", -1, True))
    print(client.simGetSegmentationObjectID('grass_mesh6_167'))

    print(client.simSetSegmentationObjectID('BP_Sky_Shere[\w]*', -1, True))
    print(client.simSetSegmentationObjectID('BP_sandy_slope[\w]*', -1, True))
    print(client.simSetSegmentationObjectID('Landscape[\w]*', 50, True))
    print(client.simSetSegmentationObjectID('Water[\w]*', 20, True))

    print(client.simSetSegmentationObjectID("SM_beech_tree[\w]*", 80, True))
    print(client.simSetSegmentationObjectID("BF_mesh_firewood[\w]*", 255, True))
    print(client.simSetSegmentationObjectID("grass_mesh[\w]*", 255, True))
    print(client.simSetSegmentationObjectID('bridge_2', 200))

    # 多线程
    t1 = Thread(target=th1)
    t2 = Thread(target=th2)
    t3 = Thread(target=th3)
    t4 = Thread(target=th4)
    t5 = Thread(target=th5)
    t6 = Thread(target=th6)
    # t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()
    # t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
    print("主线程结束")
