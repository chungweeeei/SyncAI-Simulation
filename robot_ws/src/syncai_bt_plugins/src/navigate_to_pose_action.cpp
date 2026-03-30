#include "syncai_bt_plugins/navigate_to_pose_action.hpp"

#include <tf2/LinearMath/Quaternion.h>

namespace syncai_bt_plugins
{

NavigateToPoseAction::NavigateToPoseAction(
  const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
}

BT::NodeStatus NavigateToPoseAction::onStart()
{
  if (!config().blackboard->get<rclcpp::Node::SharedPtr>("node", node_)) {
    throw BT::RuntimeError("Missing 'node' in blackboard");
  }

  double x, y, yaw;
  if (!getInput("x", x) || !getInput("y", y)) {
    throw BT::RuntimeError("Missing required input port: x or y");
  }
  getInput("yaw", yaw);

  goal_done_ = false;
  goal_success_ = false;
  goal_handle_ = nullptr;

  action_client_ = rclcpp_action::create_client<Nav2NavigateToPose>(
    node_, "navigate_to_pose");

  if (!action_client_->wait_for_action_server(std::chrono::seconds(10))) {
    RCLCPP_ERROR(node_->get_logger(), "[NavigateToPose] Action server not available");
    return BT::NodeStatus::FAILURE;
  }

  auto goal = Nav2NavigateToPose::Goal();
  goal.pose.header.frame_id = "map";
  goal.pose.header.stamp = node_->now();
  goal.pose.pose.position.x = x;
  goal.pose.pose.position.y = y;

  tf2::Quaternion q;
  q.setRPY(0, 0, yaw);
  goal.pose.pose.orientation.x = q.x();
  goal.pose.pose.orientation.y = q.y();
  goal.pose.pose.orientation.z = q.z();
  goal.pose.pose.orientation.w = q.w();

  RCLCPP_INFO(node_->get_logger(),
    "[NavigateToPose] Sending goal: x=%.2f, y=%.2f, yaw=%.2f", x, y, yaw);

  auto send_goal_options = rclcpp_action::Client<Nav2NavigateToPose>::SendGoalOptions();
  send_goal_options.result_callback =
    [this](const GoalHandle::WrappedResult & result) {
      goal_done_ = true;
      goal_success_ = (result.code == rclcpp_action::ResultCode::SUCCEEDED);
    };

  auto future = action_client_->async_send_goal(goal, send_goal_options);
  if (future.wait_for(std::chrono::seconds(15)) != std::future_status::ready) {
    RCLCPP_ERROR(node_->get_logger(), "[NavigateToPose] Failed to send goal");
    return BT::NodeStatus::FAILURE;
  }

  goal_handle_ = future.get();
  if (!goal_handle_) {
    RCLCPP_ERROR(node_->get_logger(), "[NavigateToPose] Goal was rejected");
    return BT::NodeStatus::FAILURE;
  }

  RCLCPP_INFO(node_->get_logger(), "[NavigateToPose] Goal accepted");
  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus NavigateToPoseAction::onRunning()
{
  if(!goal_done_){
    return BT::NodeStatus::RUNNING;
  }

  if (!goal_success_) {
    RCLCPP_WARN(node_->get_logger(), "[NavigateToPose] Failed");
    return BT::NodeStatus::FAILURE;
  }

  RCLCPP_INFO(node_->get_logger(), "[NavigateToPose] Succeeded");
  return BT::NodeStatus::SUCCESS;
}

void NavigateToPoseAction::onHalted()
{
  if (goal_handle_) {
    action_client_->async_cancel_goal(goal_handle_);
    RCLCPP_INFO(node_->get_logger(), "[NavigateToPose] Halted, goal cancelled");
  }
  goal_handle_ = nullptr;
  action_client_.reset();
}

}  // namespace syncai_bt_plugins
