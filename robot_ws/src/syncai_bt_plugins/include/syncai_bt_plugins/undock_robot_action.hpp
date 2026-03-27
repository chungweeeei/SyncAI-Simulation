#ifndef SYNCAI_BT_PLUGINS__UNDOCK_ROBOT_ACTION_HPP_
#define SYNCAI_BT_PLUGINS__UNDOCK_ROBOT_ACTION_HPP_

#include <string>
#include <memory>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "nav2_msgs/action/undock_robot.hpp"

namespace syncai_bt_plugins
{

class UndockRobotAction : public BT::StatefulActionNode
{
public:
  using UndockRobot = nav2_msgs::action::UndockRobot;
  using GoalHandle = rclcpp_action::ClientGoalHandle<UndockRobot>;

  UndockRobotAction(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts()
  {
    return {
      BT::InputPort<std::string>("dock_type", "simple_charging_dock", "Type of dock to undock from"),
    };
  }

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  rclcpp::Node::SharedPtr node_;
  rclcpp_action::Client<UndockRobot>::SharedPtr action_client_;
  GoalHandle::SharedPtr goal_handle_;
  bool goal_done_{false};
  bool goal_success_{false};
};

}  // namespace syncai_bt_plugins

#endif  // SYNCAI_BT_PLUGINS__UNDOCK_ROBOT_ACTION_HPP_
