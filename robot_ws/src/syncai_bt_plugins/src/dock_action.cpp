#include <cmath>

#include "syncai_bt_plugins/dock_action.hpp"

namespace syncai_bt_plugins
{

DockAction::DockAction(
  const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
}

BT::NodeStatus DockAction::onStart()
{
  if (!config().blackboard->get<rclcpp::Node::SharedPtr>("node", node_)) {
    throw BT::RuntimeError("Missing 'node' in blackboard");
  }

  double dock_x, dock_y, dock_yaw;
  std::string dock_frame;
  getInput("dock_x", dock_x);
  getInput("dock_y", dock_y);
  getInput("dock_yaw", dock_yaw);
  getInput("dock_frame", dock_frame);

  goal_done_ = false;
  goal_success_ = false;
  goal_handle_ = nullptr;

  // register dock robot ros2 action client
  action_client_ = rclcpp_action::create_client<DockRobot>(node_, "dock_robot");

  // wait for the action server to be available, right now we use opennav_docking this docking package
  if (!action_client_->wait_for_action_server(std::chrono::seconds(10))) {
    RCLCPP_ERROR(node_->get_logger(), "[Dock] Action server not available");
    return BT::NodeStatus::FAILURE;
  }

  // create and send action goal with pose-based docking
  auto goal = DockRobot::Goal();
  goal.use_dock_id = false;
  goal.dock_type = "simple_charging_dock";
  goal.navigate_to_staging_pose = true;

  goal.dock_pose.header.frame_id = dock_frame;
  goal.dock_pose.header.stamp = node_->get_clock()->now();
  goal.dock_pose.pose.position.x = dock_x;
  goal.dock_pose.pose.position.y = dock_y;
  goal.dock_pose.pose.position.z = 0.0;
  goal.dock_pose.pose.orientation.z = std::sin(dock_yaw / 2.0);
  goal.dock_pose.pose.orientation.w = std::cos(dock_yaw / 2.0);

  RCLCPP_INFO(node_->get_logger(),
    "[Dock] Sending goal: pose=(%.2f, %.2f, %.2f) frame=%s nav_to_staging=true",
    dock_x, dock_y, dock_yaw, dock_frame.c_str());

  auto send_goal_options = rclcpp_action::Client<DockRobot>::SendGoalOptions();
  send_goal_options.result_callback =
    [this](const GoalHandle::WrappedResult & result) {
      goal_done_ = true;
      goal_success_ = (result.code == rclcpp_action::ResultCode::SUCCEEDED);
    };

  auto future = action_client_->async_send_goal(goal, send_goal_options);
  if (future.wait_for(std::chrono::seconds(15)) != std::future_status::ready) {
    RCLCPP_ERROR(node_->get_logger(), "[Dock] Failed to send goal");
    return BT::NodeStatus::FAILURE;
  }

  goal_handle_ = future.get();
  if (!goal_handle_) {
    RCLCPP_ERROR(node_->get_logger(), "[Dock] Goal was rejected");
    return BT::NodeStatus::FAILURE;
  }

  RCLCPP_INFO(node_->get_logger(), "[Dock] Goal accepted");
  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus DockAction::onRunning()
{
  if(!goal_done_){
    return BT::NodeStatus::RUNNING;
  }

  if(!goal_success_){
    RCLCPP_WARN(node_->get_logger(), "[Dock] Failed");
    return BT::NodeStatus::FAILURE;
  }

  RCLCPP_INFO(node_->get_logger(), "[Dock] Succeeded");
  return BT::NodeStatus::SUCCESS;
}

void DockAction::onHalted()
{
  if (goal_handle_) {
    action_client_->async_cancel_goal(goal_handle_);
    RCLCPP_INFO(node_->get_logger(), "[Dock] Halted, goal cancelled");
  }
  goal_handle_ = nullptr;
  action_client_.reset();
}

}  // namespace syncai_bt_plugins
