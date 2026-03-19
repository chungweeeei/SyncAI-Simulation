# ROS 2 Project Guidelines

## Introduction
You are an expert ROS 2 (Robot Operating System) software engineer. When generating code, configuration, or documentation for this project, you must adhere to the following standards:

### 1. Core Technical Stack
- **ROS 2 Distribution**: Jazzy
- **Programming Languages**: C++20 or Python 3.10+
- **Build System**: colcon (ament_cmake or ament_python)

### 2. Coding Conventions & Style
#### C++ Standards
- **Component-based Design**: Always prefer inheriting from rclcpp::Node.
- **Memory Management**: Use std::shared_ptr and std::make_shared for nodes and communication interfaces.
- **Logging**: Use RCLCPP_INFO, RCLCPP_WARN, RCLCPP_ERROR macros instead of std::cout.
- **Naming**: Follow ROS 2 official style: CamelCase for classes, snake_case for variables, functions, and file names.
- **Header Guards**: Use #ifndef PROJECT_NAME__FILE_NAME_HPP_ format.

#### Python Standards
- **Entry Points**: Ensure setup.py includes correct entry points for scripts.
- **Type Hinting**: Mandatory type hints for function arguments and return values.
- **Logging**: Use node.get_logger().info() and avoid print().

### 3. ROS 2 Patterns & Best Practices
- **Timers**: Use create_wall_timer for periodic tasks instead of manual loops.
- **Parameters**: Always declare parameters using this->declare_parameter<type>("name", default_value) in the constructor.
- **QoS Profiles**: Use rclcpp::SensorDataQoS() for high-frequency sensor streams. Use rclcpp::SystemDefaultsQoS() for general command/status.
- **Launch Files**: Write launch files in Python (launch and launch_ros modules) and place them in the launch/ directory.
- **Interfaces**: Place custom .msg, .srv, and .action files in a dedicated interfaces package if the project grows.

### 4. Build System Configuration
CMakeLists.txt:
Use find_package(ament_cmake REQUIRED).
Use ament_target_dependencies(target_name ...) instead of target_link_libraries for ROS dependencies.
Ensure ament_package() is at the very end.
package.xml: Always maintain correct <depend>, <build_depend>, and <exec_depend> tags.

### 5. Strict Constraints (Avoid these mistakes)
DO NOT use ROS 1 (rospy/roscpp) syntax or headers.
DO NOT use while(rclcpp::ok()) with blocking code inside a node; use rclcpp::spin(node) or rclcpp::spin_some(node).
DO NOT hardcode topic names or frame IDs; use parameters or local constants.