#ifndef SYNCAI_BT_PLUGINS__DOOR_CONTROL_ACTION_HPP_
#define SYNCAI_BT_PLUGINS__DOOR_CONTROL_ACTION_HPP_

#include <string>
#include <chrono>
#include <atomic>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/bool.hpp"
#include "std_msgs/msg/string.hpp"

namespace syncai_bt_plugins
{

class DoorControlAction : public BT::StatefulActionNode
{
public:
  DoorControlAction(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts()
  {
    return {
      BT::InputPort<std::string>("cmd_topic", "Topic to publish door command"),
      BT::InputPort<std::string>("state_topic", "Topic to subscribe for door state"),
      BT::InputPort<bool>("open", true, "true=open, false=close"),
      BT::InputPort<double>("timeout_sec", 10.0, "Timeout in seconds"),
    };
  }

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  rclcpp::Node::SharedPtr node_;
  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr cmd_pub_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr state_sub_;
  std::atomic<bool> door_reached_target_{false};
  std::string current_state_;
  bool target_open_{true};  // true=open, false=close
  std::chrono::steady_clock::time_point start_time_;
  double timeout_sec_{10.0};
};

}  // namespace syncai_bt_plugins

#endif  // SYNCAI_BT_PLUGINS__DOOR_CONTROL_ACTION_HPP_
