#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "behaviortree_cpp/bt_factory.h"

#include "syncai_bt_plugins/action/door_control.hpp"
#include "syncai_bt_plugins/door_control_action.hpp"

using DoorControl = syncai_bt_plugins::action::DoorControl;
using GoalHandleDoorControl = rclcpp_action::ServerGoalHandle<DoorControl>;

class DoorControlServer : public rclcpp::Node
{
public:
  explicit DoorControlServer(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("door_control_server", options)
  {
    this->declare_parameter("bt_xml_file", "");

    bt_xml_file_ = this->get_parameter("bt_xml_file").as_string();
    if (bt_xml_file_.empty()) {
      RCLCPP_ERROR(this->get_logger(), "bt_xml_file parameter is required");
      return;
    }

    // Register BT plugins
    factory_.registerNodeType<syncai_bt_plugins::DoorControlAction>("DoorControl");

    // Create action server
    action_server_ = rclcpp_action::create_server<DoorControl>(
      this,
      "door_control",
      std::bind(&DoorControlServer::handle_goal, this,
        std::placeholders::_1, std::placeholders::_2),
      std::bind(&DoorControlServer::handle_cancel, this,
        std::placeholders::_1),
      std::bind(&DoorControlServer::handle_accepted, this,
        std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(), "[DoorControlServer] Ready, bt_xml: %s", bt_xml_file_.c_str());
  }

private:
  rclcpp_action::GoalResponse handle_goal(
    const rclcpp_action::GoalUUID & /*uuid*/,
    std::shared_ptr<const DoorControl::Goal> /*goal*/)
  {
    RCLCPP_INFO(this->get_logger(), "[DoorControlServer] Received goal");
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse handle_cancel(
    const std::shared_ptr<GoalHandleDoorControl> /*goal_handle*/)
  {
    RCLCPP_INFO(this->get_logger(), "[DoorControlServer] Cancel requested");
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void handle_accepted(const std::shared_ptr<GoalHandleDoorControl> goal_handle)
  {
    std::thread{std::bind(&DoorControlServer::execute, this, goal_handle)}.detach();
  }

  void execute(const std::shared_ptr<GoalHandleDoorControl> goal_handle)
  {
    auto goal = goal_handle->get_goal();
    auto result = std::make_shared<DoorControl::Result>();
    auto feedback = std::make_shared<DoorControl::Feedback>();

    const char * action_str = goal->open ? "open" : "close";

    // Set up blackboard
    auto blackboard = BT::Blackboard::create();
    blackboard->set<rclcpp::Node::SharedPtr>("node", shared_from_this());
    blackboard->set<std::string>("cmd_topic", goal->cmd_topic);
    blackboard->set<std::string>("state_topic", goal->state_topic);
    blackboard->set<bool>("open", goal->open);
    blackboard->set<double>("timeout_sec", goal->timeout_sec);

    // Create BT from XML
    BT::Tree tree;
    try {
      tree = factory_.createTreeFromFile(bt_xml_file_, blackboard);
    } catch (const std::exception & e) {
      RCLCPP_ERROR(this->get_logger(), "[DoorControlServer] Failed to create BT: %s", e.what());
      result->success = false;
      result->message = std::string("BT creation failed: ") + e.what();
      goal_handle->abort(result);
      return;
    }

    // Tick loop
    const auto tick_period = std::chrono::milliseconds(100);
    BT::NodeStatus status = BT::NodeStatus::RUNNING;

    feedback->status = goal->open ? "WAITING_FOR_DOOR_OPEN" : "WAITING_FOR_DOOR_CLOSE";
    goal_handle->publish_feedback(feedback);

    while (rclcpp::ok() && status == BT::NodeStatus::RUNNING) {
      if (goal_handle->is_canceling()) {
        tree.haltTree();
        result->success = false;
        result->message = "Cancelled";
        goal_handle->canceled(result);
        RCLCPP_INFO(this->get_logger(), "[DoorControlServer] Goal cancelled");
        return;
      }

      status = tree.tickOnce();
      std::this_thread::sleep_for(tick_period);
    }

    if (status == BT::NodeStatus::SUCCESS) {
      result->success = true;
      result->message = std::string("Door ") + (goal->open ? "opened" : "closed");
      feedback->status = goal->open ? "DOOR_OPENED" : "DOOR_CLOSED";
      goal_handle->publish_feedback(feedback);
      goal_handle->succeed(result);
      RCLCPP_INFO(this->get_logger(), "[DoorControlServer] Door %s successfully", action_str);
    } else {
      result->success = false;
      result->message = std::string("Failed to ") + action_str + " door";
      goal_handle->abort(result);
      RCLCPP_WARN(this->get_logger(), "[DoorControlServer] Failed to %s door", action_str);
    }
  }

  std::string bt_xml_file_;
  BT::BehaviorTreeFactory factory_;
  rclcpp_action::Server<DoorControl>::SharedPtr action_server_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<DoorControlServer>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
