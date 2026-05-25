#include "syncai_driver_manager/syncai_driver_manager.hpp"

namespace syncai_driver_manager
{

DriverManagerNode::DriverManagerNode(const rclcpp::NodeOptions & options)
: Node("syncai_driver_manager", options)
{
    timer_cb_group_ = this->create_callback_group(rclcpp::CallbackGroupType::MutuallyExclusive);
    service_cb_group_ = this->create_callback_group(rclcpp::CallbackGroupType::MutuallyExclusive);

    declare_parameters();
    get_parameters();
    init_pub_sub();

    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode] Node initialized successfully");
}

void DriverManagerNode::declare_parameters()
{
    this->declare_parameter("battery_initial_level", 100.0);
    this->declare_parameter("battery_discharge_rate", 0.1); // % per second
    this->declare_parameter("battery_charge_rate", 0.5);    // % per second
    this->declare_parameter("battery_publish_rate", 1.0);   // Hz
    this->declare_parameter("robot_frame_id", "base_link");
    this->declare_parameter("robot_type", "amr");
}

void DriverManagerNode::get_parameters()
{
    battery_level_ = this->get_parameter("battery_initial_level").as_double();
    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode][get_parameters] battery_initial_level: %f", battery_level_);

    battery_discharge_rate_ = this->get_parameter("battery_discharge_rate").as_double();
    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode][get_parameters] battery_discharge_rate: %f", battery_discharge_rate_);

    battery_charge_rate_ = this->get_parameter("battery_charge_rate").as_double();
    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode][get_parameters] battery_charge_rate: %f", battery_charge_rate_);

    is_charging_ = false;

    battery_publish_rate_ = this->get_parameter("battery_publish_rate").as_double();
    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode][get_parameters] battery_publish_rate: %f", battery_publish_rate_);

    robot_frame_id_ = this->get_parameter("robot_frame_id").as_string();
    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode][get_parameters] robot_frame_id: %s", robot_frame_id_.c_str());

    robot_type_ = this->get_parameter("robot_type").as_string();
    RCLCPP_INFO(this->get_logger(), "[DriverManagerNode][get_parameters] robot_type: %s", robot_type_.c_str());
}

void DriverManagerNode::init_pub_sub()
{
    battery_pub_ = this->create_publisher<sensor_msgs::msg::BatteryState>("battery_state", rclcpp::QoS(10));

    start_recharge_srv_ = this->create_service<std_srvs::srv::Trigger>(
        "start_recharge",
        std::bind(&DriverManagerNode::start_recharge_callback, this,
                  std::placeholders::_1, std::placeholders::_2),
        rclcpp::ServicesQoS(),
        service_cb_group_);

    stop_recharge_srv_ = this->create_service<std_srvs::srv::Trigger>(
        "stop_recharge",
        std::bind(&DriverManagerNode::stop_recharge_callback, this,
                  std::placeholders::_1, std::placeholders::_2),
        rclcpp::ServicesQoS(),
        service_cb_group_);

    set_battery_level_srv_ = this->create_service<syncai_common::srv::SetBatteryLevel>(
        "set_battery_level",
        std::bind(&DriverManagerNode::set_battery_level_callback, this,
                  std::placeholders::_1, std::placeholders::_2),
        rclcpp::ServicesQoS(),
        service_cb_group_);

    auto period = std::chrono::duration<double>(1.0 / battery_publish_rate_);
    battery_timer_ = this->create_wall_timer(
        std::chrono::duration_cast<std::chrono::milliseconds>(period),
        std::bind(&DriverManagerNode::battery_timer_callback, this),
        timer_cb_group_
    );
}

void DriverManagerNode::battery_timer_callback()
{
    std::lock_guard<std::mutex> lock(state_mutex_);
    if (robot_type_ == "robot_dog") {
        battery_level_ = 100.0;
        is_charging_ = false;
    } else if (is_charging_) {
        battery_level_ += battery_charge_rate_ / battery_publish_rate_;
        battery_level_ = std::min(100.0, battery_level_);
        if (battery_level_ >= 100.0) {
            is_charging_ = false;
            RCLCPP_INFO(this->get_logger(), "[DriverManagerNode] Battery fully charged, charging stopped");
        }
    } else {
        battery_level_ -= battery_discharge_rate_ / battery_publish_rate_;
        battery_level_ = std::max(0.0, battery_level_);
    }

    sensor_msgs::msg::BatteryState msg;
    msg.header.stamp = this->now();
    msg.header.frame_id = robot_frame_id_;

    msg.percentage = static_cast<float>(static_cast<int>(battery_level_));
    msg.voltage = static_cast<float>(20.0 + (battery_level_ / 100.0) * 5.2);  // 20V~25.2V
    msg.current = 2.5f;
    msg.temperature = 35.0f;

    if (is_charging_) {
        msg.power_supply_status = sensor_msgs::msg::BatteryState::POWER_SUPPLY_STATUS_CHARGING;
    } else if (battery_level_ >= 100.0) {
        msg.power_supply_status = sensor_msgs::msg::BatteryState::POWER_SUPPLY_STATUS_FULL;
    } else {
        msg.power_supply_status = sensor_msgs::msg::BatteryState::POWER_SUPPLY_STATUS_DISCHARGING;
    }

    battery_pub_->publish(msg);

    if (!is_charging_ && battery_level_ < 20.0 && battery_level_ > 0.0) {
        RCLCPP_WARN(this->get_logger(), "Low battery: %.1f%%", battery_level_);
    }
}

void DriverManagerNode::start_recharge_callback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request> /*request*/,
    std::shared_ptr<std_srvs::srv::Trigger::Response> response)
{
    std::lock_guard<std::mutex> lock(state_mutex_);
    bool was_charging = is_charging_;
    is_charging_ = true;
    response->success = true;
    if (was_charging) {
        response->message = "Already charging";
        RCLCPP_INFO(this->get_logger(),
            "[DriverManagerNode] start_recharge: already charging at %.1f%%", battery_level_);
    } else {
        response->message = "Charging started";
        RCLCPP_INFO(this->get_logger(),
            "[DriverManagerNode] start_recharge: charging started at %.1f%%", battery_level_);
    }
}

void DriverManagerNode::stop_recharge_callback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request> /*request*/,
    std::shared_ptr<std_srvs::srv::Trigger::Response> response)
{
    std::lock_guard<std::mutex> lock(state_mutex_);
    bool was_charging = is_charging_;
    is_charging_ = false;
    response->success = true;
    if (was_charging) {
        response->message = "Charging stopped";
        RCLCPP_INFO(this->get_logger(),
            "[DriverManagerNode] stop_recharge: charging stopped at %.1f%%", battery_level_);
    } else {
        response->message = "Not charging";
        RCLCPP_INFO(this->get_logger(),
            "[DriverManagerNode] stop_recharge: was not charging (battery %.1f%%)", battery_level_);
    }
}

void DriverManagerNode::set_battery_level_callback(
    const std::shared_ptr<syncai_common::srv::SetBatteryLevel::Request> request,
    std::shared_ptr<syncai_common::srv::SetBatteryLevel::Response> response)
{
    if (request->battery_level < 0.0 || request->battery_level > 100.0) {
        response->success = false;
        response->message = "Battery level must be between 0.0 and 100.0";
        RCLCPP_WARN(this->get_logger(),
            "[DriverManagerNode] set_battery_level rejected: %.1f out of range",
            request->battery_level);
        return;
    }

    std::lock_guard<std::mutex> lock(state_mutex_);
    battery_level_ = request->battery_level;
    response->success = true;
    response->message = "Battery level set to " + std::to_string(request->battery_level);
    RCLCPP_INFO(this->get_logger(),
        "[DriverManagerNode] Battery level set to %.1f%%", request->battery_level);
}

}// namespace syncai_driver_manager

int main(int argc, char ** argv){
    rclcpp::init(argc, argv);
    auto node = std::make_shared<syncai_driver_manager::DriverManagerNode>();
    rclcpp::executors::MultiThreadedExecutor executor;
    executor.add_node(node);
    executor.spin();
    rclcpp::shutdown();
    return 0;
}


