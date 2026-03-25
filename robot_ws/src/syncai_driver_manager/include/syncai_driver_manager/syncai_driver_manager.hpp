#ifndef SYNCAI_DRIVER_MANAGER__SYNCAI_DRIVER_MANAGER_HPP_
#define SYNCAI_DRIVER_MANAGER__SYNCAI_DRIVER_MANAGER_HPP_

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/battery_state.hpp>
#include <std_srvs/srv/trigger.hpp>

namespace syncai_driver_manager
{

class DriverManagerNode : public rclcpp::Node
{
public:
    explicit DriverManagerNode(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());
private:
    void declare_parameters();
    void get_parameters();
    void init_pub_sub();

    void battery_timer_callback();
    void recharge_callback(
        const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
        std::shared_ptr<std_srvs::srv::Trigger::Response> response);

    // Publishers
    rclcpp::Publisher<sensor_msgs::msg::BatteryState>::SharedPtr battery_pub_;

    // Services
    rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr recharge_srv_;

    // Timers
    rclcpp::TimerBase::SharedPtr battery_timer_;

    // Battery parameters
    double battery_level_;
    double battery_discharge_rate_;  // % per second
    double battery_publish_rate_;    // Hz
    std::string robot_frame_id_;
};
} // namespace syncai_driver_manager


# endif // SYNCAI_DRIVER_MANAGER__SYNCAI_DRIVER_MANAGER_HPP_