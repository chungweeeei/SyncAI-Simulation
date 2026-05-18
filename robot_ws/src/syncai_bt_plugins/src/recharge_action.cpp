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

  std::string start_service, stop_service, battery_topic;
  getInput("start_service", start_service);
  getInput("stop_service", stop_service);
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

  // Create both clients up-front so onHalted can call stop even if onRunning never reaches target.
  start_client_ = node_->create_client<std_srvs::srv::Trigger>(start_service);
  stop_client_ = node_->create_client<std_srvs::srv::Trigger>(stop_service);

  if (!start_client_->wait_for_service(std::chrono::seconds(10))) {
    RCLCPP_ERROR(node_->get_logger(),
      "[Recharge] Start service '%s' not available", start_service.c_str());
    return BT::NodeStatus::FAILURE;
  }

  auto request = std::make_shared<std_srvs::srv::Trigger::Request>();
  auto future = start_client_->async_send_request(request).future.share();

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
        "[Recharge] Start service call failed: %s", response->message.c_str());
      return BT::NodeStatus::FAILURE;
    }
  }

  RCLCPP_ERROR(node_->get_logger(), "[Recharge] Start service call timed out");
  return BT::NodeStatus::FAILURE;
}

BT::NodeStatus RechargeAction::onRunning()
{
  float pct = current_percentage_.load();

  if (pct >= target_percentage_) {
    RCLCPP_INFO(node_->get_logger(),
      "[Recharge] Battery reached %.0f%%, charging complete", pct);

    // Idempotent stop — driver_manager auto-stops at 100% but we send explicit
    // stop for safety and to support target_percentage < 100.
    if (charging_started_ && stop_client_) {
      auto request = std::make_shared<std_srvs::srv::Trigger::Request>();
      stop_client_->async_send_request(request);
    }

    battery_sub_.reset();
    start_client_.reset();
    stop_client_.reset();
    return BT::NodeStatus::SUCCESS;
  }

  return BT::NodeStatus::RUNNING;
}

void RechargeAction::onHalted()
{
  // Charge cancelled mid-flight — explicitly stop charging on the simulator.
  if (charging_started_ && stop_client_) {
    auto request = std::make_shared<std_srvs::srv::Trigger::Request>();
    stop_client_->async_send_request(request);
    RCLCPP_INFO(node_->get_logger(), "[Recharge] Halted, sent stop_recharge request");
  }
  battery_sub_.reset();
  start_client_.reset();
  stop_client_.reset();
  charging_started_ = false;
}

}  // namespace syncai_bt_plugins
