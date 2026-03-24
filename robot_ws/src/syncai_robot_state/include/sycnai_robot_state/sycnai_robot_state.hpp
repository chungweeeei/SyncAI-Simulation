#ifndef SYNCAI_ROBOT_STATE__SYNCAI_ROBOT_STATE_HPP_
#define SYNCAI_ROBOT_STATE__SYNCAI_ROBOT_STATE_HPP_

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/battery_state.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>
#include <syncai_common/msg/robot_state.hpp>

namespace syncai_robot_state
{
class RobotStateNode: public rclcpp::Node
{
public:
    explicit RobotStateNode(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());

private:
    void declare_parameters();
    void get_parameters();
    void init_pub_sub();

    void robot_state_timer_callback();
    void battery_callback(const sensor_msgs::msg::BatteryState::SharedPtr msg);
    void odom_callback(const nav_msgs::msg::Odometry::SharedPtr msg);

    // TF
    std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
    std::shared_ptr<tf2_ros::TransformListener> tf_listener_;

    // Subscribers
    rclcpp::Subscription<sensor_msgs::msg::BatteryState>::SharedPtr battery_sub_;
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;

    // Publishers
    rclcpp::Publisher<syncai_common::msg::RobotState>::SharedPtr robot_state_pub_;

    // Timers
    rclcpp::TimerBase::SharedPtr robot_state_timer_;

    // Parameters
    std::string robot_id_;
    std::string robot_name_;
    std::string map_name_;
    std::string model_;
    double publish_rate_;

    // Cached battery
    float battery_percentage_{0.0f};
    float battery_voltage_{0.0f};

    // Cached velocity
    geometry_msgs::msg::Twist current_velocity_;
};
} // namespace syncai_robot_state

#endif // SYNCAI_ROBOT_STATE__SYNCAI_ROBOT_STATE_HPP_