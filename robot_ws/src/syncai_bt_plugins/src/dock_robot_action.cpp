#include "syncai_bt_plugins/dock_robot_action.hpp"

namespace syncai_bt_plugins
{

DockRobotAction::DockRobotAction(
  const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
}

BT::NodeStatus DockRobotAction::onStart()
{
  if (!config().blackboard->get<rclcpp::Node::SharedPtr>("node", node_)) {
    throw BT::RuntimeError("Missing 'node' in blackboard");
  }

  std::string dock_id;
  bool navigate_to_staging = false;
  getInput("dock_id", dock_id);
  getInput("navigate_to_staging", navigate_to_staging);

  goal_done_ = false;
  goal_success_ = false;
  goal_handle_ = nullptr;

  action_client_ = rclcpp_action::create_client<DockRobot>(node_, "dock_robot");

  if (!action_client_->wait_for_action_server(std::chrono::seconds(10))) {
    RCLCPP_ERROR(node_->get_logger(), "[DockRobot] Action server not available");
    return BT::NodeStatus::FAILURE;
  }

  auto goal = DockRobot::Goal();
  goal.use_dock_id = true;
  goal.dock_id = dock_id;
  goal.navigate_to_staging_pose = navigate_to_staging;

  RCLCPP_INFO(node_->get_logger(),
    "[DockRobot] Sending goal: dock_id=%s, nav_to_staging=%s",
    dock_id.c_str(), navigate_to_staging ? "true" : "false");

  auto send_goal_options = rclcpp_action::Client<DockRobot>::SendGoalOptions();
  send_goal_options.result_callback =
    [this](const GoalHandle::WrappedResult & result) {
      goal_done_ = true;
      goal_success_ = (result.code == rclcpp_action::ResultCode::SUCCEEDED);
    };

  auto future = action_client_->async_send_goal(goal, send_goal_options);
  if (future.wait_for(std::chrono::seconds(15)) != std::future_status::ready) {
    RCLCPP_ERROR(node_->get_logger(), "[DockRobot] Failed to send goal");
    return BT::NodeStatus::FAILURE;
  }

  goal_handle_ = future.get();
  if (!goal_handle_) {
    RCLCPP_ERROR(node_->get_logger(), "[DockRobot] Goal was rejected");
    return BT::NodeStatus::FAILURE;
  }

  RCLCPP_INFO(node_->get_logger(), "[DockRobot] Goal accepted");
  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus DockRobotAction::onRunning()
{
  if (goal_done_) {
    if (goal_success_) {
      RCLCPP_INFO(node_->get_logger(), "[DockRobot] Succeeded");
      return BT::NodeStatus::SUCCESS;
    } else {
      RCLCPP_WARN(node_->get_logger(), "[DockRobot] Failed");
      return BT::NodeStatus::FAILURE;
    }
  }
  return BT::NodeStatus::RUNNING;
}

void DockRobotAction::onHalted()
{
  if (goal_handle_) {
    action_client_->async_cancel_goal(goal_handle_);
    RCLCPP_INFO(node_->get_logger(), "[DockRobot] Halted, goal cancelled");
  }
  goal_handle_ = nullptr;
  action_client_.reset();
}

}  // namespace syncai_bt_plugins
