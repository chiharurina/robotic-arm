#!/bin/bash

echo "🚀 Starting DOFBOT Demo System..."

# 1. Start Docker container if not running
if ! docker ps | grep -q ros2_dofbot; then
    echo "🔧 Starting ROS container..."
    docker start ros2_dofbot > /dev/null 2>&1
else
    echo "✅ ROS container already running"
fi

# 2. Kill old ROS node if running (safe reset)
docker exec ros2_dofbot pkill -f driver_node 2>/dev/null

# 3. Start ROS driver node in background
echo "🤖 Starting ROS driver node..."
docker exec -d ros2_dofbot bash -lc "
source /opt/ros/jazzy/setup.bash
source /root/ros2_dofbot_ws/install/setup.bash
ros2 run dofbot_driver driver_node
"

sleep 2

echo ""
echo "✅ System Ready!"
echo ""
echo "👉 Run CLI commands:"
echo "   python3 ~/my_dofbot_cli/cli_robot.py \"say hello and point left\""
echo ""
echo "👉 Run voice mode:"
echo "   source ~/my_dofbot_cli/.venv/bin/activate"
echo "   python3 ~/my_dofbot_cli/voice_robot.py"
echo ""
echo "👉 Test ROS directly:"
echo "   docker exec -it ros2_dofbot bash"
echo "   source /opt/ros/jazzy/setup.bash"
echo "   source /root/ros2_dofbot_ws/install/setup.bash"
echo "   ros2 service call /wave_hand std_srvs/srv/Trigger"
echo ""
