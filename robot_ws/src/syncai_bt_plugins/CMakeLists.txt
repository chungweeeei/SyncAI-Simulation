cmake_minimum_required(VERSION 3.8)
project(syncai_bt_plugins)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Generate action interfaces
rosidl_generate_interfaces(${PROJECT_NAME}
  "action/DoorControl.action"
  "action/Charging.action"
  "action/NavigateThroughDoor.action"
)

# --- Door Control BT plugin ---
add_library(syncai_door_control_action_bt_node SHARED
  src/door_control_action.cpp
)
target_include_directories(syncai_door_control_action_bt_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(syncai_door_control_action_bt_node PUBLIC cxx_std_20)
ament_target_dependencies(syncai_door_control_action_bt_node
  rclcpp
  behaviortree_cpp
  std_msgs
)

# --- Charging BT plugin (shared library with all charging BT nodes) ---
add_library(syncai_charging_bt_nodes SHARED
  src/navigate_to_pose_action.cpp
  src/dock_action.cpp
  src/recharge_action.cpp
  src/undock_action.cpp
)
target_include_directories(syncai_charging_bt_nodes PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(syncai_charging_bt_nodes PUBLIC cxx_std_20)
ament_target_dependencies(syncai_charging_bt_nodes
  rclcpp
  rclcpp_action
  behaviortree_cpp
  nav2_msgs
  geometry_msgs
  std_srvs
  sensor_msgs
  tf2
)

# --- Door Control action server executable ---
add_executable(door_control_server src/door_control_server.cpp)
target_include_directories(door_control_server PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(door_control_server PUBLIC cxx_std_20)
ament_target_dependencies(door_control_server
  rclcpp
  rclcpp_action
  behaviortree_cpp
  std_msgs
)

# Link door_control_server to generated action interfaces and BT plugin
rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} rosidl_typesupport_cpp)
target_link_libraries(door_control_server "${cpp_typesupport_target}")
target_link_libraries(door_control_server syncai_door_control_action_bt_node)

# --- Charging action server executable ---
add_executable(charging_server src/charging_server.cpp)
target_include_directories(charging_server PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(charging_server PUBLIC cxx_std_20)
ament_target_dependencies(charging_server
  rclcpp
  rclcpp_action
  behaviortree_cpp
  nav2_msgs
  geometry_msgs
  std_srvs
  sensor_msgs
  tf2
)
target_link_libraries(charging_server "${cpp_typesupport_target}")
target_link_libraries(charging_server syncai_charging_bt_nodes)

# --- NavigateThroughDoor action server executable ---
add_executable(navigate_through_door_server src/navigate_through_door_server.cpp)
target_include_directories(navigate_through_door_server PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(navigate_through_door_server PUBLIC cxx_std_20)
ament_target_dependencies(navigate_through_door_server
  rclcpp
  rclcpp_action
  behaviortree_cpp
  std_msgs
  nav2_msgs
  geometry_msgs
  tf2
)
target_link_libraries(navigate_through_door_server "${cpp_typesupport_target}")
target_link_libraries(navigate_through_door_server syncai_charging_bt_nodes)
target_link_libraries(navigate_through_door_server syncai_door_control_action_bt_node)

# Install
install(TARGETS
  syncai_door_control_action_bt_node
  syncai_charging_bt_nodes
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(TARGETS
  door_control_server
  charging_server
  navigate_through_door_server
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/
  DESTINATION include
)

install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
