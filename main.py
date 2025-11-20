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
client.simSetWeatherParameter(airsim.WeatherParameter.Rain, 0.75);


# unlock
client.armDisarm(True)

# Async methods returns Future. Call join() to wait for task to complete.
client.takeoffAsync().join()
client.landAsync().join()

# lock
client.armDisarm(False)

# release control
client.enableApiControl(False)