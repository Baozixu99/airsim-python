import airsim
import time
import threading


# Function to control a single UAV with a unique flight path
def control_uav(client, uav_name, path_corners):
    # Take control, arm, and take off
    client.enableApiControl(True, uav_name)
    client.armDisarm(True, uav_name)
    client.takeoffAsync(vehicle_name=uav_name).join()

    # Ascend to the starting altitude
    client.moveToZAsync(-30, 1, vehicle_name=uav_name).join()

    # Follow the specified path
    for corner in path_corners:
        client.moveToPositionAsync(corner[0], corner[1], -30, 1, vehicle_name=uav_name).join()

    # Land, disarm, and release control
    client.landAsync(vehicle_name=uav_name).join()
    client.armDisarm(False, uav_name)
    client.enableApiControl(False, uav_name)


# Connect to the AirSim simulator
client = airsim.MultirotorClient()
client.confirmConnection()

# Define unique paths for each UAV (as a list of waypoints)
paths = {
    'UAV1': [(30, 0), (30, 30), (0, 30), (0, 0)],
    'UAV2': [(60, 0), (60, 60), (0, 60), (0, 0)],
    'UAV3': [(90, 0), (90, 90), (0, 90), (0, 0)]
}

# Create and start a thread for each UAV
threads = []
for uav_name, path_corners in paths.items():
    t = threading.Thread(target=control_uav, args=(client, uav_name, path_corners))
    threads.append(t)
    t.start()

# Wait for all threads to complete
for t in threads:
    t.join()

print("All UAVs have completed their flight paths.")
