#ifndef SYNCAI_BT_PLUGINS__DOCK_ACTION_HPP_
#define SYNCAI_BT_PLUGINS__DOCK_ACTION_HPP_

#include <string>
#include <memory>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "nav2_msgs/action/dock_robot.hpp"

namespace syncai_bt_plugins
{

class DockAction : public BT::StatefulActionNode
{
public:
  using DockRobot = nav2_msgs::action::DockRobot;
  using GoalHandle = rclcpp_action::ClientGoalHandle<DockRobot>;

  DockAction(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts()
  {
    return {
      BT::InputPort<std::string>("dock_id", "charging_station", "Dock ID from database"),
      BT::InputPort<bool>("navigate_to_staging", false, "Navigate to staging pose before docking"),
    };
  }

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  rclcpp::Node::SharedPtr node_;
  rclcpp_action::Client<DockRobot>::SharedPtr action_client_;
  GoalHandle::SharedPtr goal_handle_;
  bool goal_done_{false};
  bool goal_success_{false};
};

}  // namespace syncai_bt_plugins

#endif  // SYNCAI_BT_PLUGINS__DOCK_ROBOT_ACTION_HPP_
