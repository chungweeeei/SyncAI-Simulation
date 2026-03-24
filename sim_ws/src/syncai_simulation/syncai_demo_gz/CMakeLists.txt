cmake_minimum_required(VERSION 3.8)
project(syncai_demo_gz)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED COMPONENTS register)
find_package(gz-transport13 REQUIRED)
find_package(gz-msgs10 REQUIRED)

# Door Plugin
add_library(DoorPlugin SHARED src/DoorPlugin.cc)
target_link_libraries(DoorPlugin
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2-register
  gz-transport13::gz-transport13
  gz-msgs10::gz-msgs10
)

# Alarm Plugin
add_library(AlarmPlugin SHARED src/AlarmPlugin.cc)
target_link_libraries(AlarmPlugin
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2-register
  gz-transport13::gz-transport13
  gz-msgs10::gz-msgs10
)

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

install(TARGETS DoorPlugin AlarmPlugin
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  models
  worlds
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
