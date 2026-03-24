# ====================
# RobotState.msg
# ====================

# Header (timestamp + frame_id)
std_msgs/Header header

# --- Device Info ---
string robot_id         # e.g "robot01"
string robot_name       # e.g "SyncBot01"
string model            # Robot model type

# --- Map ---
string map              # Active map identifier

# --- Position (map frame) ---
geometry_msgs/Pose pose

# --- Velocity ---
geometry_msgs/Twist velocity

# --- Battery --
float32 battery_percentage # 0.0 ~ 100.0%
float32 battery_voltage    # Volts

