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
find_package(rosidl_default_generators REQUIRED)

# Generate action interfaces
rosidl_generate_interfaces(${PROJECT_NAME}
  "action/DoorControl.action"
)

# BT plugin shared library
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

# Action server executable
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

# Link action server to generated action interfaces
rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} rosidl_typesupport_cpp)
target_link_libraries(door_control_server "${cpp_typesupport_target}")
target_link_libraries(door_control_server syncai_door_control_action_bt_node)

# Install
install(TARGETS syncai_door_control_action_bt_node
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(TARGETS door_control_server
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
