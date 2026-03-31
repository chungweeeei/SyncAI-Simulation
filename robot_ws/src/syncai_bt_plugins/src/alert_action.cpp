#include "syncai_bt_plugins/alert_action.hpp"

namespace syncai_bt_plugins
{

AlertAction::AlertAction(const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
}

BT::NodeStatus AlertAction::onStart()
{
  // Get ROS node from blackboard
  if (!config().blackboard->get<rclcpp::Node::SharedPtr>("node", node_)) {
    throw BT::RuntimeError("Missing 'node' in blackboard");
  }

  // Use relative topic "alert" — resolves to /<namespace>/alert
  alert_pub_ = node_->create_publisher<std_msgs::msg::Bool>("alert", rclcpp::QoS(1));

  auto msg = std_msgs::msg::Bool();
  msg.data = true;
  alert_pub_->publish(msg);

  RCLCPP_INFO(node_->get_logger(), "[AlertAction] Alert activated on %s/alert",
    node_->get_namespace());
  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus AlertAction::onRunning()
{
  // Stay running — alert remains active until halted by Parallel node
  return BT::NodeStatus::RUNNING;
}

void AlertAction::onHalted()
{
  // Publish alert OFF
  if (alert_pub_) {
    auto msg = std_msgs::msg::Bool();
    msg.data = false;
    alert_pub_->publish(msg);
    alert_pub_.reset();
  }
  RCLCPP_INFO(node_->get_logger(), "[AlertAction] Alert deactivated");
}

}  // namespace syncai_bt_plugins

#include "behaviortree_cpp/bt_factory.h"
BT_REGISTER_NODES(factory)
{
  factory.registerNodeType<syncai_bt_plugins::AlertAction>("Alert");
}
