#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "behaviortree_cpp/bt_factory.h"

#include "syncai_bt_plugins/action/navigate_with_alert.hpp"
#include "syncai_bt_plugins/navigate_to_pose_action.hpp"
#include "syncai_bt_plugins/alert_action.hpp"

using NavigateWithAlert = syncai_bt_plugins::action::NavigateWithAlert;
using GoalHandleNWA = rclcpp_action::ServerGoalHandle<NavigateWithAlert>;

class NavigateWithAlertServer : public rclcpp::Node
{
public:
  explicit NavigateWithAlertServer(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("navigate_with_alert_server", options)
  {
    this->declare_parameter("bt_xml_file", "");

    bt_xml_file_ = this->get_parameter("bt_xml_file").as_string();
    if (bt_xml_file_.empty()) {
      RCLCPP_ERROR(this->get_logger(), "bt_xml_file parameter is required");
      return;
    }

    // Register BT plugins
    factory_.registerNodeType<syncai_bt_plugins::NavigateToPoseAction>("NavigateToPose");
    factory_.registerNodeType<syncai_bt_plugins::AlertAction>("Alert");

    // Create action server
    action_server_ = rclcpp_action::create_server<NavigateWithAlert>(
      this,
      "navigate_with_alert",
      std::bind(&NavigateWithAlertServer::handle_goal, this,
        std::placeholders::_1, std::placeholders::_2),
      std::bind(&NavigateWithAlertServer::handle_cancel, this,
        std::placeholders::_1),
      std::bind(&NavigateWithAlertServer::handle_accepted, this,
        std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(),
      "[NavigateWithAlertServer] Ready, bt_xml: %s", bt_xml_file_.c_str());
  }

private:
  rclcpp_action::GoalResponse handle_goal(
    const rclcpp_action::GoalUUID & /*uuid*/,
    std::shared_ptr<const NavigateWithAlert::Goal> /*goal*/)
  {
    RCLCPP_INFO(this->get_logger(), "[NavigateWithAlertServer] Received goal");
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse handle_cancel(
    const std::shared_ptr<GoalHandleNWA> /*goal_handle*/)
  {
    RCLCPP_INFO(this->get_logger(), "[NavigateWithAlertServer] Cancel requested");
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void handle_accepted(const std::shared_ptr<GoalHandleNWA> goal_handle)
  {
    std::thread{std::bind(&NavigateWithAlertServer::execute, this, goal_handle)}.detach();
  }

  void execute(const std::shared_ptr<GoalHandleNWA> goal_handle)
  {
    auto goal = goal_handle->get_goal();
    auto result = std::make_shared<NavigateWithAlert::Result>();
    auto feedback = std::make_shared<NavigateWithAlert::Feedback>();

    // Set up blackboard with all goal fields
    auto blackboard = BT::Blackboard::create();
    blackboard->set<rclcpp::Node::SharedPtr>("node", shared_from_this());
    blackboard->set<double>("target_x", goal->target_x);
    blackboard->set<double>("target_y", goal->target_y);
    blackboard->set<double>("target_yaw", goal->target_yaw);

    // Create BT from XML
    BT::Tree tree;
    try {
      tree = factory_.createTreeFromFile(bt_xml_file_, blackboard);
    } catch (const std::exception & e) {
      RCLCPP_ERROR(this->get_logger(),
        "[NavigateWithAlertServer] Failed to create BT: %s", e.what());
      result->success = false;
      result->message = std::string("BT creation failed: ") + e.what();
      goal_handle->abort(result);
      return;
    }

    // Tick loop
    const auto tick_period = std::chrono::milliseconds(100);
    BT::NodeStatus status = BT::NodeStatus::RUNNING;

    while (rclcpp::ok() && status == BT::NodeStatus::RUNNING) {
      if (goal_handle->is_canceling()) {
        tree.haltTree();
        result->success = false;
        result->message = "Cancelled";
        goal_handle->canceled(result);
        RCLCPP_INFO(this->get_logger(), "[NavigateWithAlertServer] Goal cancelled");
        return;
      }

      status = tree.tickOnce();

      // Collect status from both parallel children for composite feedback
      std::string nav_status = "IDLE";
      std::string alert_status = "IDLE";

      auto visitor = [&nav_status, &alert_status](BT::TreeNode * node) {
        std::string name = node->name();
        if (name == "NavigateToPose") {
          nav_status = (node->status() == BT::NodeStatus::RUNNING) ? "NAVIGATING" :
                       (node->status() == BT::NodeStatus::SUCCESS) ? "ARRIVED" : "NAV_FAILED";
        } else if (name == "Alert") {
          alert_status = (node->status() == BT::NodeStatus::RUNNING) ? "ALERTING" :
                         (node->status() == BT::NodeStatus::IDLE) ? "ALERT_OFF" : "ALERT_OFF";
        }
      };
      tree.applyVisitor(visitor);

      std::string step = nav_status + "+" + alert_status;
      if (feedback->current_step != step) {
        feedback->current_step = step;
        goal_handle->publish_feedback(feedback);
      }

      std::this_thread::sleep_for(tick_period);
    }

    if (status == BT::NodeStatus::SUCCESS) {
      result->success = true;
      result->message = "Navigate with alert completed";
      feedback->current_step = "ARRIVED+ALERT_OFF";
      goal_handle->publish_feedback(feedback);
      goal_handle->succeed(result);
      RCLCPP_INFO(this->get_logger(),
        "[NavigateWithAlertServer] Completed successfully");
    } else {
      result->success = false;
      result->message = "Failed at: " + feedback->current_step;
      goal_handle->abort(result);
      RCLCPP_WARN(this->get_logger(),
        "[NavigateWithAlertServer] Failed at: %s", feedback->current_step.c_str());
    }
  }

  std::string bt_xml_file_;
  BT::BehaviorTreeFactory factory_;
  rclcpp_action::Server<NavigateWithAlert>::SharedPtr action_server_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<NavigateWithAlertServer>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
