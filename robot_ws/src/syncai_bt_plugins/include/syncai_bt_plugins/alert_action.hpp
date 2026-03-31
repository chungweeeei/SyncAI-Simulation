#ifndef SYNCAI_BT_PLUGINS__ALERT_ACTION_HPP_
#define SYNCAI_BT_PLUGINS__ALERT_ACTION_HPP_

#include <string>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/bool.hpp"

namespace syncai_bt_plugins
{

class AlertAction : public BT::StatefulActionNode
{
public:
  AlertAction(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts()
  {
    return {};
  }

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  rclcpp::Node::SharedPtr node_;
  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr alert_pub_;
};

}  // namespace syncai_bt_plugins

#endif  // SYNCAI_BT_PLUGINS__ALERT_ACTION_HPP_
