cmake_minimum_required(VERSION 3.8)
project(syncai_robot_sim_gz_plugins)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(gz-sim8 REQUIRED)  # Harmonic; 用 gz-sim7 如果是 Garden
find_package(gz-plugin2 REQUIRED)
find_package(syncai_robot_sim_common REQUIRED)
find_package(Eigen3 REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)

add_library(diff_drive SHARED src/diff_drive.cpp)

target_link_libraries(diff_drive
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2)

ament_target_dependencies(diff_drive
  rclcpp syncai_robot_sim_common)

target_include_directories(diff_drive PRIVATE ${EIGEN3_INCLUDE_DIRS})

install(TARGETS diff_drive
  LIBRARY DESTINATION lib)

ament_environment_hooks(
  "${ament_cmake_package_templates_ENVIRONMENT_HOOK_LIBRARY_PATH}")

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
