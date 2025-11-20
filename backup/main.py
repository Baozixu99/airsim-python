"""
 test python environment
 """
import airsim

# connect to the AirSim simulator
client = airsim.MultirotorClient()
client.confirmConnection()

# get control
client.enableApiControl(True)

print(client.simListAssets())

client.simEnableWeather(True)

# airsim.wait_key('Press any key to enable rain at 25%')
# client.simSetWeatherParameter(airsim.WeatherParameter.Rain, 0.25);
# airsim.wait_key('Press any key to enable rain at 75%')
# client.simSetWeatherParameter(airsim.WeatherParameter.Rain, 0.75);


# unlock
client.armDisarm(True)

# Async methods returns Future. Call join() to wait for task to complete.
client.takeoffAsync().join()
client.simSetTimeOfDay(True, start_datetime="24:00:00")
client.landAsync().join()

# lock
client.armDisarm(False)

# release control
client.enableApiControl(False)
client.simEnableWeather(True)

# client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0.25)
# poacherList = client.simListSceneObjects()
# all_dict = {item: "others" for item in poacherList }
# huopao_dict = {item: "huopao" for item in poacherList if item.startswith("huopao")}
# tank_static_dict = {item: "tank" for item in poacherList if item.startswith("tank") or item.startswith("BP_tank") or item.startswith("BP_West_Tank") or item.startswith("Tank")}
# tank_moving_dict = {item: "tank" for item in poacherList if  item.startswith("BP_tank")  or item.startswith("Tank")}
# soldier_dict = {item: "soldier" for item in poacherList if item.startswith("SM_Modular_soldier") or item.startswith("BP_Soldier")}
# truck_dict = {item: "truck" for item in poacherList if item.startswith("军用车1")}
# truck_move_wheel_dict = {item: "truck_wheel" for item in poacherList if  item.startswith("军用车1_wheel1") or item.startswith("军用车1_wheel9") or item.startswith("军用车1_wheel2")}
# truck_move_cabin_dict = {item: "truck_cabin" for item in poacherList if item.startswith("军用车1_cabin4") or item.startswith("军用车1_cabin3")}
# truck_move_frame_dict = {item: "truck_frame" for item in poacherList if item.startswith("军用车1_frame4") or item.startswith("军用车1_frame3")}
# land_dict = {item: "land" for item in poacherList if item.startswith("Landscape")}
# Guard_room_dict = {item: "Guard_room" for item in poacherList if item.startswith("Guard")}
# all_dict.update(huopao_dict)
# all_dict.update(tank_static_dict)
# all_dict.update(tank_moving_dict)
# all_dict.update(soldier_dict)
# all_dict.update(truck_dict)
# all_dict.update(truck_move_wheel_dict)
# all_dict.update(truck_move_cabin_dict)
# all_dict.update(truck_move_frame_dict)
# all_dict.update(land_dict)
# all_dict.update(Guard_room_dict)

