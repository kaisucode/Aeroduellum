import numpy as np
from blocklyTranslations import *
from droneManagement import DroneManagement
from wand_logger_with_drone import WandFollower
import time

from action_detector import *
import queue


def main():
    sim = False
    multiplayer = True
    if sim:
        # Use sim version of crazyswarm
        from pycrazyswarm import Crazyswarm

        # from ros_sim import Node, TFMessage, rclpy, Joy
        rclpy = rclpy_sim
        swarm = Crazyswarm(args="--vis=null --sim")
        crazyflies = swarm.allcfs.crazyflies
        timeHelper = swarm.timeHelper

        groupState = SimpleNamespace(crazyflies=crazyflies, timeHelper=timeHelper)
    else:
        # Use real ROS
        from tf2_msgs.msg import TFMessage
        from rclpy.node import Node
        import rclpy
        from crazyflie_py import Crazyswarm
        from sensor_msgs.msg import Joy

        swarm = Crazyswarm()
        crazyflies = swarm.allcfs.crazyflies
        timeHelper = swarm.timeHelper

        groupState = SimpleNamespace(crazyflies=crazyflies, timeHelper=timeHelper)

    print("Taking off") 
    takeoff(groupState, 1.0, 3)
    timeHelper.sleep(3.0)

    max_time = time.time() + 240
    _exec = rclpy.executors.MultiThreadedExecutor()
    print("Setting up game, multiplayer is ", ("on" if multiplayer else "off"))
    # Create groups for each player's drones
    p1_crazyflies = SimpleNamespace(crazyflies=crazyflies[0:4], timeHelper=timeHelper)
    # Start Wand Follower Nodes
    p1_wand_node = WandFollower(p1_crazyflies, timeHelper, max_time=max_time, player=1)
    # Start Drone Management Nodes
    p1_dm = DroneManagement(p1_crazyflies, player=1)
    if multiplayer:
        p2_crazyflies = SimpleNamespace(
            crazyflies=crazyflies[4:8], timeHelper=timeHelper
        )
        p2_wand_node = WandFollower(p2_crazyflies, timeHelper, max_time=max_time, player=2)
        p2_dm = DroneManagement(p2_crazyflies, player=2)

    print("Going to start positions")
    for idx in range(4):
        p1_dm.initialize_drone_position(p1_dm.groupState, idx, 1, max_time)
        if multiplayer:
            p2_dm.initialize_drone_position(p2_dm.groupState, idx, 2, max_time)

    # Game loop
    p1 = True
    p2 = True
    print("Starting game loop")
    _exec.add_node(p1_wand_node)
    _exec.add_node(p1_dm)
    _exec.add_node(p2_wand_node)
    _exec.add_node(p2_dm)
    try:
        _exec.spin()
    finally:
        print("Shutting Down")
        _exec.shutdown()

    print("Landing Drones")
    land(groupState, 0.01, 3)
    timeHelper.sleep(3.0)
    print("Shutdown Complete")


main()
