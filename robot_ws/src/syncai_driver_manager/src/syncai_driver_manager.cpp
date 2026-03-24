#include "syncai_driver_manager/syncai_driver_manager.hpp"

namespace syncai_driver_manager
{

DriverManagerNode::DriverManagerNode(const rclcpp::NodeOptions & options)
: Node("syncai_driver_manager", options)
{
    declare_parameters();
    get_parameters();
    init_pub_sub();

    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode] Node initialized successfully");
}

void DriverManagerNode::declare_parameters()
{
    this->declare_parameter("battery_initial_level", 100.0);
    this->declare_parameter("battery_discharge_rate", 0.1); // % per second
    this->declare_parameter("battery_publish_rate", 1.0);   // Hz
    this->declare_parameter("robot_frame_id", "base_link");
}

void DriverManagerNode::get_parameters()
{
    battery_level_ = this->get_parameter("battery_initial_level").as_double();
    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode][get_parameters] battery_initial_level: %f", battery_level_);

    battery_discharge_rate_ = this->get_parameter("battery_discharge_rate").as_double();
    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode][get_parameters] battery_discharge_rate: %f", battery_discharge_rate_);

    battery_publish_rate_ = this->get_parameter("battery_publish_rate").as_double();
    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode][get_parameters] battery_publish_rate: %f", battery_publish_rate_);

    robot_frame_id_ = this->get_parameter("robot_frame_id").as_string();
    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode][get_parameters] robot_frame_id: %s", robot_frame_id_.c_str());
}

void DriverManagerNode::init_pub_sub()
{
    battery_pub_ = this->create_publisher<sensor_msgs::msg::BatteryState>("battery_state", rclcpp::QoS(10));

    auto period = std::chrono::duration<double>(1.0 / battery_publish_rate_);
    battery_timer_ = this->create_wall_timer(
        std::chrono::duration_cast<std::chrono::milliseconds>(period),
        std::bind(&DriverManagerNode::battery_timer_callback, this)
    );
}

void DriverManagerNode::battery_timer_callback()
{
    // Simulate discharge
    battery_level_ -= battery_discharge_rate_ / battery_publish_rate_;
    battery_level_ = std::max(0.0, battery_level_);

    sensor_msgs::msg::BatteryState msg;
    msg.header.stamp = this->now();
    msg.header.frame_id = robot_frame_id_;

    msg.percentage = static_cast<float>(static_cast<int>(battery_level_));
    msg.voltage = static_cast<float>(20.0 + (battery_level_ / 100.0) * 5.2);  // 20V~25.2V
    msg.current = 2.5f;
    msg.temperature = 35.0f;

    battery_pub_->publish(msg);

    if(battery_level_ < 20.0 && battery_level_ > 0.0){
        RCLCPP_WARN(this->get_logger(), "Low battery: %.1f%%", battery_level_);
    }
}

}// namespace syncai_driver_manager

int main(int argc, char ** argv){
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<syncai_driver_manager::DriverManagerNode>());
    rclcpp::shutdown();
    return 0;
}


