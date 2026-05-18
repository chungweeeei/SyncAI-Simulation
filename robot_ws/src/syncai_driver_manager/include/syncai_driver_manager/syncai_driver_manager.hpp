#ifndef SYNCAI_DRIVER_MANAGER__SYNCAI_DRIVER_MANAGER_HPP_
#define SYNCAI_DRIVER_MANAGER__SYNCAI_DRIVER_MANAGER_HPP_

#include <mutex>

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/battery_state.hpp>
#include <std_srvs/srv/trigger.hpp>
#include <syncai_common/srv/set_battery_level.hpp>

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
    void start_recharge_callback(
        const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
        std::shared_ptr<std_srvs::srv::Trigger::Response> response);
    void stop_recharge_callback(
        const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
        std::shared_ptr<std_srvs::srv::Trigger::Response> response);
    void set_battery_level_callback(
        const std::shared_ptr<syncai_common::srv::SetBatteryLevel::Request> request,
        std::shared_ptr<syncai_common::srv::SetBatteryLevel::Response> response);

    // Publishers
    rclcpp::Publisher<sensor_msgs::msg::BatteryState>::SharedPtr battery_pub_;

    // Services
    rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr start_recharge_srv_;
    rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr stop_recharge_srv_;
    rclcpp::Service<syncai_common::srv::SetBatteryLevel>::SharedPtr set_battery_level_srv_;

    // Timers
    rclcpp::TimerBase::SharedPtr battery_timer_;

    // Callback groups
    rclcpp::CallbackGroup::SharedPtr timer_cb_group_;
    rclcpp::CallbackGroup::SharedPtr service_cb_group_;

    // Thread safety
    std::mutex state_mutex_;

    // Battery parameters
    double battery_level_;
    double battery_discharge_rate_;  // % per second
    double battery_charge_rate_;     // % per second
    double battery_publish_rate_;    // Hz
    bool is_charging_;
    std::string robot_frame_id_;
};
} // namespace syncai_driver_manager


# endif // SYNCAI_DRIVER_MANAGER__SYNCAI_DRIVER_MANAGER_HPP_