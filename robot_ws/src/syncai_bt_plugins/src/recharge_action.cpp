#include "syncai_bt_plugins/recharge_action.hpp"

namespace syncai_bt_plugins
{

RechargeAction::RechargeAction(
  const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
}

BT::NodeStatus RechargeAction::onStart()
{
  if (!config().blackboard->get<rclcpp::Node::SharedPtr>("node", node_)) {
    throw BT::RuntimeError("Missing 'node' in blackboard");
  }

  std::string service_name, battery_topic;
  getInput("service_name", service_name);
  getInput("battery_topic", battery_topic);
  getInput("target_percentage", target_percentage_);

  charging_started_ = false;
  current_percentage_.store(0.0f);

  // Subscribe to battery state
  battery_sub_ = node_->create_subscription<sensor_msgs::msg::BatteryState>(
    battery_topic, rclcpp::QoS(10),
    [this](const sensor_msgs::msg::BatteryState::SharedPtr msg) {
      current_percentage_.store(msg->percentage);
    });

  // Call recharge service to start charging
  service_client_ = node_->create_client<std_srvs::srv::Trigger>(service_name);

  if (!service_client_->wait_for_service(std::chrono::seconds(10))) {
    RCLCPP_ERROR(node_->get_logger(),
      "[Recharge] Service '%s' not available", service_name.c_str());
    return BT::NodeStatus::FAILURE;
  }

  auto request = std::make_shared<std_srvs::srv::Trigger::Request>();
  auto future = service_client_->async_send_request(request).future.share();

  if (future.wait_for(std::chrono::seconds(5)) == std::future_status::ready) {
    auto response = future.get();
    if (response->success) {
      charging_started_ = true;
      RCLCPP_INFO(node_->get_logger(),
        "[Recharge] %s, waiting for battery to reach %.0f%%",
        response->message.c_str(), target_percentage_);
      return BT::NodeStatus::RUNNING;
    } else {
      RCLCPP_WARN(node_->get_logger(),
        "[Recharge] Service call failed: %s", response->message.c_str());
      return BT::NodeStatus::FAILURE;
    }
  }

  RCLCPP_ERROR(node_->get_logger(), "[Recharge] Service call timed out");
  return BT::NodeStatus::FAILURE;
}

BT::NodeStatus RechargeAction::onRunning()
{
  float pct = current_percentage_.load();

  if (pct >= target_percentage_) {
    RCLCPP_INFO(node_->get_logger(),
      "[Recharge] Battery reached %.0f%%, charging complete", pct);
    battery_sub_.reset();
    service_client_.reset();
    return BT::NodeStatus::SUCCESS;
  }

  return BT::NodeStatus::RUNNING;
}

void RechargeAction::onHalted()
{
  // If charging was started, call service again to toggle it off
  if (charging_started_ && service_client_) {
    auto request = std::make_shared<std_srvs::srv::Trigger::Request>();
    service_client_->async_send_request(request);
    RCLCPP_INFO(node_->get_logger(), "[Recharge] Halted, sent stop charging request");
  }
  battery_sub_.reset();
  service_client_.reset();
  charging_started_ = false;
}

}  // namespace syncai_bt_plugins
