#include "syncai_bt_plugins/undock_action.hpp"

namespace syncai_bt_plugins
{

UndockAction::UndockAction(
  const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
}

BT::NodeStatus UndockAction::onStart()
{
  if (!config().blackboard->get<rclcpp::Node::SharedPtr>("node", node_)) {
    throw BT::RuntimeError("Missing 'node' in blackboard");
  }

  std::string dock_type;
  getInput("dock_type", dock_type);

  goal_done_ = false;
  goal_success_ = false;
  goal_handle_ = nullptr;

  action_client_ = rclcpp_action::create_client<UndockRobot>(node_, "undock_robot");

  if (!action_client_->wait_for_action_server(std::chrono::seconds(10))) {
    RCLCPP_ERROR(node_->get_logger(), "[Undock] Action server not available");
    return BT::NodeStatus::FAILURE;
  }

  auto goal = UndockRobot::Goal();
  goal.dock_type = dock_type;

  RCLCPP_INFO(node_->get_logger(),
    "[Undock] Sending goal: dock_type=%s", dock_type.c_str());

  auto send_goal_options = rclcpp_action::Client<UndockRobot>::SendGoalOptions();
  send_goal_options.result_callback =
    [this](const GoalHandle::WrappedResult & result) {
      goal_done_ = true;
      goal_success_ = (result.code == rclcpp_action::ResultCode::SUCCEEDED);
    };

  auto future = action_client_->async_send_goal(goal, send_goal_options);
  if (future.wait_for(std::chrono::seconds(15)) != std::future_status::ready) {
    RCLCPP_ERROR(node_->get_logger(), "[Undock] Failed to send goal");
    return BT::NodeStatus::FAILURE;
  }

  goal_handle_ = future.get();
  if (!goal_handle_) {
    RCLCPP_ERROR(node_->get_logger(), "[Undock] Goal was rejected");
    return BT::NodeStatus::FAILURE;
  }

  RCLCPP_INFO(node_->get_logger(), "[Undock] Goal accepted");
  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus UndockAction::onRunning()
{
  if (!goal_done_) {
    return BT::NodeStatus::RUNNING;
  }

  if (!goal_success_) {
    RCLCPP_WARN(node_->get_logger(), "[Undock] Failed");
    return BT::NodeStatus::FAILURE;
  }
  
  RCLCPP_INFO(node_->get_logger(), "[Undock] Succeeded");
  return BT::NodeStatus::SUCCESS;
}

void UndockAction::onHalted()
{
  if (goal_handle_) {
    action_client_->async_cancel_goal(goal_handle_);
    RCLCPP_INFO(node_->get_logger(), "[Undock] Halted, goal cancelled");
  }
  goal_handle_ = nullptr;
  action_client_.reset();
}

}  // namespace syncai_bt_plugins
