#include "syncai_robot_state/sycnai_robot_state.hpp"

namespace syncai
{ 

RobotStateNode::RobotStateNode(const rclcpp::NodeOptions & options)
: Node("robot_state_node", options)
{
    declare_parameters();
    get_parameters();

    init_pub_sub();
    RCLCPP_INFO(this->get_logger(), "[RobotStateNode] Node initialized successfully");
}

void RobotStateNode::declare_parameters()
{
    this->declare_parameter("battery_initial_level", 100.0);
    this->declare_parameter("battery_discharge_rate", 0.1); // % per second
    this->declare_parameter("battery_publish_rate", 1.0);   // Hz
    this->declare_parameter("robot_frame", "base_link");
}

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

void RobotStateNode::init_pub_sub()
{
    // Create subscribers
    odom_sub_ = this->create_subscription<nav_msgs::msg::Odometry>(
        "odom", rclcpp::QoS(10), 
        std::bind(&RobotStateNode::odom_callback, this, std::placeholders::_1));

    // Create publishers
    pose_pub_ = this->create_publisher<geometry_msgs::msg::PoseStamped>("robot_pose", 10);
    battery_pub_ = this->create_publisher<sensor_msgs::msg::BatteryState>("battery_state", 10);

    // Create timer for battery state update
    auto period = std::chrono::duration<double>(1.0 / battery_publish_rate_);
    battery_timer_ = this->create_wall_timer(
        std::chrono::duration_cast<std::chrono::milliseconds>(period),
        std::bind(&RobotStateNode::battery_timer_callback, this)
    );
}

void RobotStateNode::odom_callback(const nav_msgs::msg::Odometry::SharedPtr msg)
{
    geometry_msgs::msg::PoseStamped pose_msg;
    pose_msg.header = msg->header;
    pose_msg.header.frame_id = robot_frame_;
    pose_msg.pose = msg->pose.pose;

    pose_pub_->publish(pose_msg);
}

void RobotStateNode::battery_timer_callback()
{
    // Discharge battery(simulate)
    battery_level_ -= battery_discharge_rate_ / battery_publish_rate_;
    battery_level_ = std::max(0.0, battery_level_);

    // Publish battery state
    sensor_msgs::msg::BatteryState battery_msg;
    battery_msg.header.stamp = this->now();
    battery_msg.header.frame_id = robot_frame_;

    battery_msg.percentage = static_cast<float>(battery_level_ / 100.0);
    battery_msg.voltage = static_cast<float>(20.0 + (battery_level_ / 100.0) * 5.2);
    battery_msg.current = 2.5f;
    battery_msg.temperature = 35.0f;
    if (battery_level_ > 20.0) {
      battery_msg.power_supply_status = sensor_msgs::msg::BatteryState::POWER_SUPPLY_STATUS_DISCHARGING;
    } else {
      battery_msg.power_supply_status = sensor_msgs::msg::BatteryState::POWER_SUPPLY_STATUS_NOT_CHARGING;
    }

    battery_msg.power_supply_health = sensor_msgs::msg::BatteryState::POWER_SUPPLY_HEALTH_GOOD;
    battery_msg.power_supply_technology = sensor_msgs::msg::BatteryState::POWER_SUPPLY_TECHNOLOGY_LIPO;
    battery_msg.present = true;

    battery_pub_->publish(battery_msg);

    if (battery_level_ < 20.0 && battery_level_ > 0.0) {
      RCLCPP_WARN(this->get_logger(), "Low battery: %.1f%%", battery_level_);
    }
}
    
} // namespace syncai

int main(int argc, char ** argv){
    rclcpp::init(argc, argv);
    auto node = std::make_shared<syncai::RobotStateNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}