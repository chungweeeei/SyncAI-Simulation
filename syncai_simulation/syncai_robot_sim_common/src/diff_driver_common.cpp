#include "syncai_robot_sim_common/diff_driver_common.hpp"

#include <geometry_msgs/msg/transform_stamped.hpp>
#include <tf2/LinearMath/Quaternion.h>

#include <cmath>
#include <algorithm>

namespace syncai_robot_sim_common
{
DiffDriverCommon::DiffDriverCommon() = default;

rclcpp::Logger DiffDriverCommon::logger() const {
    if (_ros_node) {
        return _ros_node->get_logger();
    } 
    return rclcpp::get_logger("diff_driver_common");
}

void DiffDriverCommon::set_model_name(const std::string &model_name) {
    _model_name = model_name;
}

std::string DiffDriverCommon::model_name() const {
    return _model_name;
}

void DiffDriverCommon::init_ros_node(const rclcpp::Node::SharedPtr node) {
    _ros_node = node;

    // Initialize subscriber and publisher
    _cmd_vel_sub = _ros_node->create_subscription<geometry_msgs::msg::Twist>(
        _config.cmd_vel_topic, 
        rclcpp::QoS(10),
        std::bind(&DiffDriverCommon::cmd_vel_callback, this, std::placeholders::_1));

    _odom_pub = _ros_node->template create_publisher<nav_msgs::msg::Odometry>(_config.odom_topic, rclcpp::QoS(10));

    _tf2_broadcaster = std::make_shared<tf2_ros::TransformBroadcaster>(_ros_node);

    RCLCPP_INFO(logger(), "DiffDriver [%s] initialized: cmd_vel='%s', odom='%s'",
      _model_name.c_str(),
      _config.cmd_vel_topic.c_str(),
      _config.odom_topic.c_str());
}


void DiffDriverCommon::cmd_vel_callback(
  const geometry_msgs::msg::Twist::SharedPtr msg) {
  std::lock_guard<std::mutex> lock(_cmd_vel_mutex);
  _latest_cmd.linear_x = std::clamp(msg->linear.x, -_config.max_linear_velocity, _config.max_linear_velocity);
  _latest_cmd.angular_z = std::clamp(msg->angular.z, -_config.max_angular_velocity, _config.max_angular_velocity);
}

DiffDriverCommon::VelocityCommand DiffDriverCommon::get_velocity_command() const {
  std::lock_guard<std::mutex> lock(_cmd_vel_mutex);
  return _latest_cmd;
}

void DiffDriverCommon::update_odometry(const Eigen::Isometry3d& pose, double time) {

    if (!_initialized_pose){
        _old_pose = pose;
        _last_update_time = time;
        _last_odom_pub_time = time;
        _initialized_pose = true;
        return;
    }

    const double dt = time - _last_update_time;
    if (dt <= 0.0) return;

    // Compute velocities from pose difference
    const Eigen::Isometry3d delta = _old_pose.inverse() * pose;
    const Eigen::Vector3d dp = delta.translation();

    // Extract yaw from pose
    const Eigen::Matrix3d rot = pose.rotation();
    const double yaw = std::atan2(rot(1, 0), rot(0, 0));
    const Eigen::Matrix3d old_rot = _old_pose.rotation();
    const double old_yaw = std::atan2(old_rot(1, 0), old_rot(0, 0));
    double dyaw = yaw - old_yaw;

    // Normalize angle
    while (dyaw > M_PI) dyaw -= 2.0 * M_PI;
    while (dyaw < -M_PI) dyaw += 2.0 * M_PI;

    const double vx = dp.x() / dt;
    const double wz = dyaw / dt;

    _old_pose = pose;
    _last_update_time = time;

    // Check if it's time to publish odometry
    const double odom_period = 1.0 / _config.odom_publish_rate;
    if ((time - _last_odom_pub_time) < odom_period) return;
    
    _last_odom_pub_time = time;

    if (!_ros_node) return;

    // Build and publish Odometry message
    nav_msgs::msg::Odometry odom_msg;
    odom_msg.header.stamp = _ros_node->now();
    odom_msg.header.frame_id = _config.odom_frame_id;
    odom_msg.child_frame_id = _config.base_frame_id;

    // Position from world pose
    odom_msg.pose.pose.position.x = pose.translation().x();
    odom_msg.pose.pose.position.y = pose.translation().y();
    odom_msg.pose.pose.position.z = pose.translation().z();

    const Eigen::Quaterniond q(pose.rotation());
    odom_msg.pose.pose.orientation.x = q.x();
    odom_msg.pose.pose.orientation.y = q.y();
    odom_msg.pose.pose.orientation.z = q.z();
    odom_msg.pose.pose.orientation.w = q.w();

    _odom_pub->publish(odom_msg);

    // Publish TF: odom -> base_link
    geometry_msgs::msg::TransformStamped tf_msg;
    tf_msg.header.stamp = odom_msg.header.stamp;
    tf_msg.header.frame_id = _config.odom_frame_id;
    tf_msg.child_frame_id = _config.base_frame_id;
    tf_msg.transform.translation.x = pose.translation().x();
    tf_msg.transform.translation.y = pose.translation().y();
    tf_msg.transform.translation.z = pose.translation().z();
    tf_msg.transform.rotation.x = q.x();
    tf_msg.transform.rotation.y = q.y();
    tf_msg.transform.rotation.z = q.z();
    tf_msg.transform.rotation.w = q.w();

    _tf2_broadcaster->sendTransform(tf_msg);
}

}