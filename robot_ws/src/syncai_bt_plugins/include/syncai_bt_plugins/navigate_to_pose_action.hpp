#ifndef SYNCAI_BT_PLUGINS__NAVIGATE_TO_POSE_ACTION_HPP_
#define SYNCAI_BT_PLUGINS__NAVIGATE_TO_POSE_ACTION_HPP_

#include <string>
#include <chrono>
#include <memory>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "nav2_msgs/action/navigate_to_pose.hpp"

namespace syncai_bt_plugins
{

class NavigateToPoseAction : public BT::StatefulActionNode
{
public:
  using Nav2NavigateToPose = nav2_msgs::action::NavigateToPose;
  using GoalHandle = rclcpp_action::ClientGoalHandle<Nav2NavigateToPose>;

  NavigateToPoseAction(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts()
  {
    return {
      BT::InputPort<double>("x", "Target x position"),
      BT::InputPort<double>("y", "Target y position"),
      BT::InputPort<double>("yaw", 0.0, "Target yaw orientation"),
    };
  }

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  rclcpp::Node::SharedPtr node_;
  rclcpp_action::Client<Nav2NavigateToPose>::SharedPtr action_client_;
  GoalHandle::SharedPtr goal_handle_;
  bool goal_done_{false};
  bool goal_success_{false};
};

}  // namespace syncai_bt_plugins

#endif  // SYNCAI_BT_PLUGINS__NAVIGATE_TO_POSE_ACTION_HPP_
