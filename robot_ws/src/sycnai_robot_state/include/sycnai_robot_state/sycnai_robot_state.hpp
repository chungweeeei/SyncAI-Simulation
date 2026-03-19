#ifndef SYCNAI_ROBOT_STATE_HPP
#define SYCNAI_ROBOT_STATE_HPP

#include <rclcpp/rclcpp.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <sensor_msgs/msg/battery_state.hpp>

namespace syncai
{
class RobotStateNode: public rclcpp::Node
{
public:
    explicit RobotStateNode(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());

private:
    void declare_parameters();
    void get_parameters();
    void init_pub_sub();

    void odom_callback(const nav_msgs::msg::Odometry::SharedPtr msg);
    void battery_timer_callback();

    // Subscribers
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub;

    // Publishers
    rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_pub;
    rclcpp::Publisher<sensor_msgs::msg::BatteryState>::SharedPtr battery_pub;

    // Timer for battery
    rclcpp::TimerBase::SharedPtr battery_timer;

    // Parameters
    double battery_level_;
    double battery_discharge_rate_; // % per second
    double battery_publish_rate_;   // Hz
    std::string robot_frame_; 
};
} // namespace syncai

#endif // SYCNAI_ROBOT_STATE_HPP