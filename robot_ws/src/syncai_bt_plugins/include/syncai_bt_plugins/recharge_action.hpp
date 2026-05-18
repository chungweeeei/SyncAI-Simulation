#ifndef SYNCAI_BT_PLUGINS__RECHARGE_ACTION_HPP_
#define SYNCAI_BT_PLUGINS__RECHARGE_ACTION_HPP_

#include <string>
#include <memory>
#include <atomic>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"
#include "std_srvs/srv/trigger.hpp"
#include "sensor_msgs/msg/battery_state.hpp"

namespace syncai_bt_plugins
{

class RechargeAction : public BT::StatefulActionNode
{
public:
  RechargeAction(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts()
  {
    return {
      BT::InputPort<std::string>("start_service", "start_recharge", "Service to start charging"),
      BT::InputPort<std::string>("stop_service", "stop_recharge", "Service to stop charging"),
      BT::InputPort<std::string>("battery_topic", "battery_state", "Battery state topic"),
      BT::InputPort<double>("target_percentage", 100.0, "Target battery percentage (0-100)"),
    };
  }

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  rclcpp::Node::SharedPtr node_;
  rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr start_client_;
  rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr stop_client_;
  rclcpp::Subscription<sensor_msgs::msg::BatteryState>::SharedPtr battery_sub_;
  std::atomic<float> current_percentage_{0.0f};
  double target_percentage_{100.0};
  bool charging_started_{false};
};

}  // namespace syncai_bt_plugins

#endif  // SYNCAI_BT_PLUGINS__RECHARGE_ACTION_HPP_
