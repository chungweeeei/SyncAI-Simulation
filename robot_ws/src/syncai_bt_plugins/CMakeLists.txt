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
  "action/NavigateWithAlert.action"
)

# --- Alert BT plugin ---
add_library(syncai_alert_action_bt_node SHARED
  src/alert_action.cpp
)
target_include_directories(syncai_alert_action_bt_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(syncai_alert_action_bt_node PUBLIC cxx_std_20)
ament_target_dependencies(syncai_alert_action_bt_node
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

rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} rosidl_typesupport_cpp)

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

# --- NavigateWithAlert action server executable ---
add_executable(navigate_with_alert_server src/navigate_with_alert_server.cpp)
target_include_directories(navigate_with_alert_server PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(navigate_with_alert_server PUBLIC cxx_std_20)
ament_target_dependencies(navigate_with_alert_server
  rclcpp
  rclcpp_action
  behaviortree_cpp
  std_msgs
  nav2_msgs
  geometry_msgs
  tf2
)
target_link_libraries(navigate_with_alert_server "${cpp_typesupport_target}")
target_link_libraries(navigate_with_alert_server syncai_charging_bt_nodes)
target_link_libraries(navigate_with_alert_server syncai_alert_action_bt_node)

# Install
install(TARGETS
  syncai_alert_action_bt_node
  syncai_charging_bt_nodes
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(TARGETS
  charging_server
  navigate_with_alert_server
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
