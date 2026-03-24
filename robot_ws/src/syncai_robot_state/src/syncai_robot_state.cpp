#include "sycnai_robot_state/sycnai_robot_state.hpp"

namespace syncai_robot_state
{

RobotStateNode::RobotStateNode(const rclcpp::NodeOptions & options)
: Node("syncai_robot_state", options)
{
    declare_parameters();
    get_parameters();

    tf_buffer_ = std::make_shared<tf2_ros::Buffer>(this->get_clock());
    tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

    init_pub_sub();

    RCLCPP_INFO(this->get_logger(), "[RobotStateNode] Node initialized successfully");
}

void RobotStateNode::declare_parameters()
{
    this->declare_parameter("robot_id", "robot01");
    this->declare_parameter("robot_name", "SyncAI Robot");
    this->declare_parameter("map_name", "default_map");
    this->declare_parameter("model", "AMR");
    this->declare_parameter("publish_rate", 1.0);
}

void RobotStateNode::get_parameters()
{
    robot_id_ = this->get_parameter("robot_id").as_string();
    RCLCPP_INFO(this->get_logger(), "[RobotStateNode][get_parameters] robot_id: %s", robot_id_.c_str());

    robot_name_ = this->get_parameter("robot_name").as_string();
    RCLCPP_INFO(this->get_logger(), "[RobotStateNode][get_parameters] robot_name: %s", robot_name_.c_str());

    map_name_ = this->get_parameter("map_name").as_string();
    RCLCPP_INFO(this->get_logger(), "[RobotStateNode][get_parameters] map_name: %s", map_name_.c_str());

    model_ = this->get_parameter("model").as_string();
    RCLCPP_INFO(this->get_logger(), "[RobotStateNode][get_parameters] model: %s", model_.c_str());

    publish_rate_ = this->get_parameter("publish_rate").as_double();
    RCLCPP_INFO(this->get_logger(), "[RobotStateNode][get_parameters] publish_rate: %f", publish_rate_);
}

void RobotStateNode::init_pub_sub()
{
    // Publisher
    robot_state_pub_ = this->create_publisher<syncai_common::msg::RobotState>("robot_state", rclcpp::QoS(5));

    // Subscribers
    battery_sub_ = this->create_subscription<sensor_msgs::msg::BatteryState>(
        "battery_state",
        rclcpp::QoS(5),
        std::bind(&RobotStateNode::battery_callback, this, std::placeholders::_1)
    );

    odom_sub_ = this->create_subscription<nav_msgs::msg::Odometry>(
        "odom",
        rclcpp::QoS(5),
        std::bind(&RobotStateNode::odom_callback, this, std::placeholders::_1)
    );

    // Timer
    auto period = std::chrono::duration<double>(1.0 / publish_rate_);
    robot_state_timer_ = this->create_wall_timer(
        std::chrono::duration_cast<std::chrono::milliseconds>(period),
        std::bind(&RobotStateNode::robot_state_timer_callback, this)
    );
}

void RobotStateNode::robot_state_timer_callback()
{
    syncai_common::msg::RobotState msg;
    msg.header.stamp = this->now();
    msg.header.frame_id = "map";

    // Device info
    msg.robot_id = robot_id_;
    msg.robot_name = robot_name_;
    msg.model = model_;

    // Map
    msg.map = map_name_;

    // Pose from TF
    try {
        auto transform = tf_buffer_->lookupTransform("map", robot_id_ + "/base_link", tf2::TimePointZero);
        msg.pose.position.x = transform.transform.translation.x;
        msg.pose.position.y = transform.transform.translation.y;
        msg.pose.position.z = transform.transform.translation.z;
        msg.pose.orientation = transform.transform.rotation;
    } catch (const tf2::TransformException & ex) {
        RCLCPP_WARN(this->get_logger(), "Could not get transform: %s", ex.what());
    }

    // Velocity
    msg.velocity = current_velocity_;

    // Battery
    msg.battery_percentage = battery_percentage_;
    msg.battery_voltage = battery_voltage_;

    robot_state_pub_->publish(msg);
}

void RobotStateNode::battery_callback(const sensor_msgs::msg::BatteryState::SharedPtr msg)
{
    battery_percentage_ = msg->percentage;
    battery_voltage_ = msg->voltage;
}

void RobotStateNode::odom_callback(const nav_msgs::msg::Odometry::SharedPtr msg)
{
    current_velocity_ = msg->twist.twist;
}

}// namespace syncai_robot_state

int main(int argc, char ** argv){
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<syncai_robot_state::RobotStateNode>());
    rclcpp::shutdown();
    return 0;
}