import time

from pynput import keyboard
import airsim

# 连接无人机，开启无人机API控制，解锁无人机，无人机起飞
client = airsim.MultirotorClient()
client.enableApiControl(True)
client.armDisarm(True)
client.takeoffAsync().join()


client.simEnableWeather(True)

# airsim.wait_key('Press any key to enable rain at 25%')
# client.simSetWeatherParameter(airsim.WeatherParameter.Rain, 0.25);
# airsim.wait_key('Press any key to enable rain at 75%')
client.simSetWeatherParameter(airsim.WeatherParameter.Rain, 0.00)


res = client.simListSceneObjects()
print(res)
res2 = client.simGetObjectPose('Fire_N_Smoke_Ref_09_A_23')
print(res2)

print(client.simGetSegmentationObjectID('Fire_01_2SubUV_blend_pt'))
print(client.simSetSegmentationObjectID('Fire_01_2SubUV_blend_pt',240))
# print(client.simGetSegmentationObjectID('SM_stones_01_8'))
# print(client.simSetSegmentationObjectID('SM_stones_01_8',240))
obj = client.simSpawnObject("LightSource","SpotLightBP",client.simGetObjectPose("LightSource"),client.simGetObjectScale("LightSource"),True,True)
print(obj)
print(client.simSetLightIntensity(obj,0.0))

client.simSetTimeOfDay(True, start_datetime = "2018-02-12 0:20:00", is_start_datetime_dst = True, celestial_clock_speed = 5000, update_interval_secs = 1, move_sun = True)

# 声明全局变量，便于长按监听
current_key = None
# 声明全局默认飞行速度
default_speed = 5
# 设置响应间隔时间
default_timeout = 10


# 键盘按下事件
def on_press(key):
    global current_key
    # 1.判断按键是否长按，若长按则不需要改变运行，非长按则需要改变运行轨迹
    if key != current_key:
        # 2.根据按键情况需要改变运行轨迹
        if key.char == 'a':
            print("往左飞")
            client.moveByVelocityAsync(0, -default_speed, 0, default_timeout)
        if key.char == 'd':
            print("往右飞")
            client.moveByVelocityAsync(0, default_speed, 0, default_timeout)
        if key.char == 'w':
            print("往前飞")
            client.moveByVelocityAsync(default_speed, 0, 0, default_timeout)
        if key.char == 's':
            print("往后飞")
            client.moveByVelocityAsync(-default_speed, 0, 0, default_timeout)
        if key.char == 'q':
            print("往上飞")
            client.moveByVelocityAsync(0, 0, -default_speed, default_timeout)
        if key.char == 'e':
            print("往下飞")
            client.moveByVelocityAsync(0, 0, default_speed, default_timeout)
        if key.char == 'g':
            print("截取红外图像")
            response = client.simGetImage("bottom_center", airsim.ImageType.Infrared)
            file = open("images/" + str(time.time_ns()) + ".png", 'wb')
            file.write(response)
            file.close()
        if key.char == 'r':
            print("雾")
            client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0.50);
        if key.char == 't':
            print("关雾")
            # client.simSetWeatherParameter(airsim.WeatherParameter.Rain, 0.00)
            client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0.00);

        current_key = key
    else:
        pass


# 键盘释放事件
def on_release(key):
    global current_key

    if key == current_key:

        # 无人机立刻悬停
        print("无人机悬停！")
        client.cancelLastTask()
        current_key = None
    if key == keyboard.Key.esc:
        return False


with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
