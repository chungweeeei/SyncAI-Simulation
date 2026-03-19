/**
 * @file sycnai_robot_state.cpp
 * @brief ROS2 node for publishing robot state information including pose and battery status.
 *
 * This node provides two main functionalities:
 * 1. Converts odometry messages to PoseStamped and republishes them
 * 2. Simulates battery discharge and publishes battery state at a configurable rate
 *
 * @author SyncAI Team
 * @date 2026
 */

#include "sycnai_robot_state/sycnai_robot_state.hpp"

namespace syncai
{ 

/**
 * @brief Constructs the RobotStateNode with the given options.
 *
 * Initializes the node by declaring and retrieving parameters,
 * then setting up publishers, subscribers, and timers.
 *
 * @param options ROS2 node options for configuration
 */
RobotStateNode::RobotStateNode(const rclcpp::NodeOptions & options)
: Node("robot_state_node", options)
{
    declare_parameters();
    get_parameters();

    init_pub_sub();
    RCLCPP_INFO(this->get_logger(), "[RobotStateNode] Node initialized successfully");
}

/**
 * @brief Declares all ROS2 parameters used by this node.
 *
 * Parameters declared:
 * - battery_initial_level: Initial battery percentage (default: 100.0)
 * - battery_discharge_rate: Battery discharge rate in % per second (default: 0.1)
 * - battery_publish_rate: Rate at which battery state is published in Hz (default: 1.0)
 * - robot_frame: TF frame ID for the robot (default: "base_link")
 */
void RobotStateNode::declare_parameters()
{
    this->declare_parameter("battery_initial_level", 100.0);
    this->declare_parameter("battery_discharge_rate", 0.1); // % per second
    this->declare_parameter("battery_publish_rate", 1.0);   // Hz
    this->declare_parameter("robot_frame", "base_link");
}

/**
 * @brief Retrieves parameter values from the ROS2 parameter server.
 *
 * Loads all declared parameters into member variables and logs
 * the retrieved values for debugging purposes.
 */
void RobotStateNode::get_parameters()
{
    battery_level_ = this->get_parameter("battery_initial_level").as_double();
    RCLCPP_INFO(this->get_logger(), "[RobotStateNode][get_parameters] battery_initial_level: %f", battery_level_);

    battery_discharge_rate_ = this->get_parameter("battery_discharge_rate").as_double();
    RCLCPP_INFO(this->get_logger(), "[RobotStateNode][get_parameters] battery_discharge_rate: %f", battery_discharge_rate_);

    battery_publish_rate_ = this->get_parameter("battery_publish_rate").as_double();
    RCLCPP_INFO(this->get_logger(), "[RobotStateNode][get_parameters] battery_publish_rate: %f", battery_publish_rate_);

    robot_frame_ = this->get_parameter("robot_frame").as_string();
    RCLCPP_INFO(this->get_logger(), "[RobotStateNode][get_parameters] robot_frame: %s", robot_frame_.c_str());
}

/**
 * @brief Initializes all publishers, subscribers, and timers.
 *
 * Sets up:
 * - Subscriber: "odom" topic for nav_msgs::msg::Odometry messages
 * - Publisher: "robot_pose" topic for geometry_msgs::msg::PoseStamped messages
 * - Publisher: "battery_state" topic for sensor_msgs::msg::BatteryState messages
 * - Timer: Periodic callback for battery state updates based on battery_publish_rate_
 */
void RobotStateNode::init_pub_sub()
{
    // Create subscriber for odometry data
    odom_sub_ = this->create_subscription<nav_msgs::msg::Odometry>(
        "odom", rclcpp::QoS(10), 
        std::bind(&RobotStateNode::odom_callback, this, std::placeholders::_1));

    // Create publishers for robot pose and battery state
    pose_pub_ = this->create_publisher<geometry_msgs::msg::PoseStamped>("robot_pose", 10);
    battery_pub_ = this->create_publisher<sensor_msgs::msg::BatteryState>("battery_state", 10);

    // Create timer for periodic battery state updates
    auto period = std::chrono::duration<double>(1.0 / battery_publish_rate_);
    battery_timer_ = this->create_wall_timer(
        std::chrono::duration_cast<std::chrono::milliseconds>(period),
        std::bind(&RobotStateNode::battery_timer_callback, this)
    );
}

/**
 * @brief Callback function for processing incoming odometry messages.
 *
 * Extracts the pose from the odometry message, wraps it in a PoseStamped
 * message with the configured robot frame, and publishes it.
 *
 * @param msg Shared pointer to the received Odometry message
 */
void RobotStateNode::odom_callback(const nav_msgs::msg::Odometry::SharedPtr msg)
{
    geometry_msgs::msg::PoseStamped pose_msg;
    pose_msg.header = msg->header;
    pose_msg.header.frame_id = robot_frame_;
    pose_msg.pose = msg->pose.pose;

    pose_pub_->publish(pose_msg);
}

/**
 * @brief Timer callback for simulating battery discharge and publishing state.
 *
 * This function:
 * 1. Decrements the battery level based on discharge rate and publish rate
 * 2. Clamps the battery level to a minimum of 0%
 * 3. Constructs and publishes a BatteryState message with simulated values:
 *    - Voltage: Linear interpolation between 20.0V (empty) and 25.2V (full)
 *    - Current: Fixed at 2.5A
 *    - Temperature: Fixed at 35.0°C
 *    - Technology: LiPo battery
 * 4. Issues a warning log when battery drops below 20%
 */
void RobotStateNode::battery_timer_callback()
{
    // Simulate battery discharge over time
    battery_level_ -= battery_discharge_rate_ / battery_publish_rate_;
    battery_level_ = std::max(0.0, battery_level_);

    // Construct battery state message with simulated values
    sensor_msgs::msg::BatteryState battery_msg;
    battery_msg.header.stamp = this->now();
    battery_msg.header.frame_id = robot_frame_;

    // Battery percentage as a fraction (0.0 to 1.0)
    battery_msg.percentage = static_cast<float>(battery_level_ / 100.0);
    // Simulate voltage: 20.0V at 0%, 25.2V at 100%
    battery_msg.voltage = static_cast<float>(20.0 + (battery_level_ / 100.0) * 5.2);
    battery_msg.current = 2.5f;       // Simulated current draw in Amps
    battery_msg.temperature = 35.0f;  // Simulated temperature in Celsius

    // Set power supply status based on battery level
    if (battery_level_ > 20.0) {
      battery_msg.power_supply_status = sensor_msgs::msg::BatteryState::POWER_SUPPLY_STATUS_DISCHARGING;
    } else {
      battery_msg.power_supply_status = sensor_msgs::msg::BatteryState::POWER_SUPPLY_STATUS_NOT_CHARGING;
    }

    battery_msg.power_supply_health = sensor_msgs::msg::BatteryState::POWER_SUPPLY_HEALTH_GOOD;
    battery_msg.power_supply_technology = sensor_msgs::msg::BatteryState::POWER_SUPPLY_TECHNOLOGY_LIPO;
    battery_msg.present = true;

    battery_pub_->publish(battery_msg);

    // Warn when battery is low but not empty
    if (battery_level_ < 20.0 && battery_level_ > 0.0) {
      RCLCPP_WARN(this->get_logger(), "Low battery: %.1f%%", battery_level_);
    }
}
    
} // namespace syncai

/**
 * @brief Main entry point for the robot_state_node executable.
 *
 * Initializes ROS2, creates the RobotStateNode, spins until shutdown,
 * then performs cleanup.
 *
 * @param argc Number of command-line arguments
 * @param argv Array of command-line argument strings
 * @return 0 on successful execution
 */
int main(int argc, char ** argv){
    rclcpp::init(argc, argv);
    auto node = std::make_shared<syncai::RobotStateNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}