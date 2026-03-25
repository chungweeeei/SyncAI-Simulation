#include "syncai_bt_plugins/door_control_action.hpp"

namespace syncai_bt_plugins
{

DoorControlAction::DoorControlAction(const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
}

BT::NodeStatus DoorControlAction::onStart()
{
  // Get ROS node from blackboard
  if (!config().blackboard->get<rclcpp::Node::SharedPtr>("node", node_)) {
    throw BT::RuntimeError("Missing 'node' in blackboard");
  }

  // Read port parameters
  std::string cmd_topic, state_topic;
  if (!getInput("cmd_topic", cmd_topic)) {
    throw BT::RuntimeError("Missing required input port: cmd_topic");
  }
  if (!getInput("state_topic", state_topic)) {
    throw BT::RuntimeError("Missing required input port: state_topic");
  }
  getInput("open", target_open_);
  getInput("timeout_sec", timeout_sec_);

  // Reset state
  door_reached_target_ = false;
  current_state_ = "";

  // Target state string: "open" or "closed"
  std::string target_str = target_open_ ? "open" : "closed";

  // Create publisher and subscriber
  cmd_pub_ = node_->create_publisher<std_msgs::msg::Bool>(cmd_topic, rclcpp::QoS(1));
  state_sub_ = node_->create_subscription<std_msgs::msg::String>(
    state_topic, rclcpp::QoS(1),
    [this, target_str](const std_msgs::msg::String::SharedPtr msg) {
      current_state_ = msg->data;
      if (msg->data == target_str) {
        door_reached_target_ = true;
      }
    });

  // Send command (true=open, false=close)
  auto cmd_msg = std_msgs::msg::Bool();
  cmd_msg.data = target_open_;
  cmd_pub_->publish(cmd_msg);

  const char * action = target_open_ ? "open" : "close";
  RCLCPP_INFO(node_->get_logger(), "[DoorControlAction] Published %s command to %s",
    action, cmd_topic.c_str());

  start_time_ = std::chrono::steady_clock::now();
  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus DoorControlAction::onRunning()
{
  if (door_reached_target_) {
    const char * action = target_open_ ? "opened" : "closed";
    RCLCPP_INFO(node_->get_logger(), "[DoorControlAction] Door %s", action);
    return BT::NodeStatus::SUCCESS;
  }

  auto elapsed = std::chrono::steady_clock::now() - start_time_;
  double elapsed_sec = std::chrono::duration<double>(elapsed).count();

  if (elapsed_sec > timeout_sec_) {
    RCLCPP_WARN(node_->get_logger(),
      "[DoorControlAction] Timeout after %.1f seconds (current state: %s)",
      elapsed_sec, current_state_.c_str());
    return BT::NodeStatus::FAILURE;
  }

  return BT::NodeStatus::RUNNING;
}

void DoorControlAction::onHalted()
{
  door_reached_target_ = false;
  current_state_ = "";
  state_sub_.reset();
  cmd_pub_.reset();
  RCLCPP_INFO(node_->get_logger(), "[DoorControlAction] Halted");
}

}  // namespace syncai_bt_plugins

#include "behaviortree_cpp/bt_factory.h"
BT_REGISTER_NODES(factory)
{
  factory.registerNodeType<syncai_bt_plugins::DoorControlAction>("DoorControl");
}
