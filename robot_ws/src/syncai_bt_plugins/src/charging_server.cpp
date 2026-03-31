#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "behaviortree_cpp/bt_factory.h"

#include "syncai_bt_plugins/action/charging.hpp"
#include "syncai_bt_plugins/navigate_to_pose_action.hpp"
#include "syncai_bt_plugins/dock_action.hpp"
#include "syncai_bt_plugins/recharge_action.hpp"
#include "syncai_bt_plugins/undock_action.hpp"

using Charging = syncai_bt_plugins::action::Charging;
using GoalHandleCharging = rclcpp_action::ServerGoalHandle<Charging>;

class ChargingServer : public rclcpp::Node
{
public:
  explicit ChargingServer(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("charging_server", options)
  {
    this->declare_parameter("bt_xml_file", "");

    bt_xml_file_ = this->get_parameter("bt_xml_file").as_string();
    if (bt_xml_file_.empty()) {
      RCLCPP_ERROR(this->get_logger(), "bt_xml_file parameter is required");
      return;
    }

    // Register BT plugins
    factory_.registerNodeType<syncai_bt_plugins::NavigateToPoseAction>("NavigateToPose");
    factory_.registerNodeType<syncai_bt_plugins::DockAction>("Dock");
    factory_.registerNodeType<syncai_bt_plugins::RechargeAction>("Recharge");
    factory_.registerNodeType<syncai_bt_plugins::UndockAction>("Undock");

    // Create action server
    action_server_ = rclcpp_action::create_server<Charging>(
      this,
      "charging",
      std::bind(&ChargingServer::handle_goal, this,
        std::placeholders::_1, std::placeholders::_2),
      std::bind(&ChargingServer::handle_cancel, this,
        std::placeholders::_1),
      std::bind(&ChargingServer::handle_accepted, this,
        std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(), "[ChargingServer] Ready, bt_xml: %s", bt_xml_file_.c_str());
  }

private:
  rclcpp_action::GoalResponse handle_goal(
    const rclcpp_action::GoalUUID & /*uuid*/,
    std::shared_ptr<const Charging::Goal> /*goal*/)
  {
    RCLCPP_INFO(this->get_logger(), "[ChargingServer] Received goal");
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse handle_cancel(
    const std::shared_ptr<GoalHandleCharging> /*goal_handle*/)
  {
    RCLCPP_INFO(this->get_logger(), "[ChargingServer] Cancel requested");
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void handle_accepted(const std::shared_ptr<GoalHandleCharging> goal_handle)
  {
    std::thread{std::bind(&ChargingServer::execute, this, goal_handle)}.detach();
  }

  void execute(const std::shared_ptr<GoalHandleCharging> goal_handle)
  {
    auto goal = goal_handle->get_goal();
    auto result = std::make_shared<Charging::Result>();
    auto feedback = std::make_shared<Charging::Feedback>();

    // Set up blackboard
    auto blackboard = BT::Blackboard::create();
    blackboard->set<rclcpp::Node::SharedPtr>("node", shared_from_this());
    blackboard->set<double>("target_x", goal->target_x);
    blackboard->set<double>("target_y", goal->target_y);
    blackboard->set<double>("target_yaw", goal->target_yaw);
    blackboard->set<std::string>("recharge_service", goal->recharge_service);

    // Create BT from XML
    BT::Tree tree;
    try {
      tree = factory_.createTreeFromFile(bt_xml_file_, blackboard);
    } catch (const std::exception & e) {
      RCLCPP_ERROR(this->get_logger(), "[ChargingServer] Failed to create BT: %s", e.what());
      result->success = false;
      result->message = std::string("BT creation failed: ") + e.what();
      goal_handle->abort(result);
      return;
    }

    // Tick loop
    const auto tick_period = std::chrono::milliseconds(100);
    BT::NodeStatus status = BT::NodeStatus::RUNNING;

    // Step names for feedback
    const std::vector<std::string> steps = {
      "DOCKING", "CHARGING", "UNDOCKING"
    };

    feedback->current_step = "DOCKING";
    goal_handle->publish_feedback(feedback);

    while (rclcpp::ok() && status == BT::NodeStatus::RUNNING) {
      if (goal_handle->is_canceling()) {
        tree.haltTree();
        result->success = false;
        result->message = "Cancelled";
        goal_handle->canceled(result);
        RCLCPP_INFO(this->get_logger(), "[ChargingServer] Goal cancelled");
        return;
      }

      status = tree.tickOnce();

      // Update feedback based on which node is running
      auto visitor = [&feedback, &goal_handle, &steps](BT::TreeNode * node) {
        if (node->status() == BT::NodeStatus::RUNNING) {
          std::string name = node->name();
          std::string step;
          if (name == "Dock") {
            step = steps[0];
          } else if (name == "Recharge") {
            step = steps[1];
          } else if (name == "Undock") {
            step = steps[2];
          }
          if (!step.empty() && feedback->current_step != step) {
            feedback->current_step = step;
            goal_handle->publish_feedback(feedback);
          }
        }
      };
      tree.applyVisitor(visitor);

      std::this_thread::sleep_for(tick_period);
    }

    if (status == BT::NodeStatus::SUCCESS) {
      result->success = true;
      result->message = "Charging sequence completed";
      feedback->current_step = "COMPLETED";
      goal_handle->publish_feedback(feedback);
      goal_handle->succeed(result);
      RCLCPP_INFO(this->get_logger(), "[ChargingServer] Sequence completed successfully");
    } else {
      result->success = false;
      result->message = "Charging sequence failed at step: " + feedback->current_step;
      goal_handle->abort(result);
      RCLCPP_WARN(this->get_logger(),
        "[ChargingServer] Failed at step: %s", feedback->current_step.c_str());
    }
  }

  std::string bt_xml_file_;
  BT::BehaviorTreeFactory factory_;
  rclcpp_action::Server<Charging>::SharedPtr action_server_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ChargingServer>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
