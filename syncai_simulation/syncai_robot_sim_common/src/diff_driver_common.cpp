#include <syncai_robot_sim_common/diff_drive_common.hpp>
#include <cmath>

namespace syncai_amr_sim_common
{
DiffDriverCommon::DiffDriverCommon()
{
}

void DiffDriverCommon::set_model_name(const std::string &model_name)
{
    _model_name = model_name;
}

std::string DiffDriverCommon::model_name() const
{
    return _model_name;
}

rclcpp::Logger DiffDriverCommon::logger() const
{
    return _ros_node->get_logger();
}

void DiffDriverCommon::init_ros_node(rclcpp::Node::SharedPtr node){
    
    _ros_node = std::move(node);
    
    // register velocity command
    _cmd_vel_sub = _ros_node->create_subscription<geometry_msgs::msg::Twist>(
        "cmd_vel", 10, std::bind(&DiffDriverCommon::cmd_vel_callback, this, std::placeholders::_1));

    // publish odometry
    _odom_pub = _ros_node->create_publisher<nav_msgs::msg::Odometry>("odom", 10);

    // TF broadcaster
    _tf_broadcaster = std::make_shared<tf2_ros::TransformBroadcaster>(_ros_node);

    RCLCPP_INFO(logger(), "DiffDriverCommon initialized for robot: %s",  _model_name.c_str());

}

void DiffDriverCommon::cmd_vel_callback(const geometry_msgs::msg::Twist::SharedPtr msg)
{
  _cmd_linear_vel = std::clamp(msg->linear.x, -_max_linear_vel, _max_linear_vel);
  _cmd_angular_vel = std::clamp(msg->angular.z, -_max_angular_vel, _max_angular_vel);
}

DiffDriverCommon::UpdateResult DiffDriverCommon::update(
    const Eigen::Isometry3d& pose, double time
){
    UpdateResult result;

    double dt = time - _last_update_time;
    _last_update_time = time;
    _pose = pose;

    if (!_initialized){
        _initialized = true;
        _last_pose = pose;
        return result;
    }

    // prevent dt from being too small or too large
    if (dt <= 0.0 || dt > 1.0){
        _last_pose = pose;
        return result;
    }

    // compute actual velocity
    Eigen::Vector3d displacement = pose.translation() - _last_pose.translation();
    double yaw = compute_yaw(pose);
    double last_yaw = compute_yaw(_last_pose);
    double dyaw = yaw - last_yaw;

    // handle angle
    if (dyaw > M_PI) dyaw -= 2.0 * M_PI;
    if (dyaw < -M_PI) dyaw += 2.0 * M_PI;

    _actual_linear_vel = displacement.head<2>().norm() / dt;
    _actual_angular_vel = dyaw / dt;

    double target_linear = apply_acceleration_limit(
      _actual_linear_vel, _cmd_linear_vel, _max_linear_accel, dt);
    double target_angular = apply_acceleration_limit(
      _actual_angular_vel, _cmd_angular_vel, _max_angular_accel, dt);

    result.linear_vel = target_linear;
    result.angular_vel = target_angular;

    // publish odometry and tf
    double odom_period = 1.0 / _odom_publish_rate;
    if (time - _last_odom_publish_time >= odom_period) {
      publish_odometry(time);
      publish_tf(time);
      _last_odom_publish_time = time;
    }

    _last_pose = pose;
    return result;
}

double DiffDriverCommon::apply_acceleration_limit(
  double current, double target, double max_accel, double dt) const
{
  double diff = target - current;
  double max_change = max_accel * dt;
  
  if (std::abs(diff) <= max_change) {
    return target;
  }
  return current + std::copysign(max_change, diff);
}

double DiffDriverCommon::compute_yaw(const Eigen::Isometry3d& pose) const
{
  Eigen::Quaterniond quat(pose.linear());
  return std::atan2(
    2.0 * (quat.w() * quat.z() + quat.x() * quat.y()),
    1.0 - 2.0 * (quat.y() * quat.y() + quat.z() * quat.z()));
}

void DiffDriverCommon::publish_odometry(double time)
{
    const int32_t t_sec = static_cast<int32_t>(time);
    const uint32_t t_nsec =
      static_cast<uint32_t>((time - static_cast<double>(t_sec)) * 1e9);
    const rclcpp::Time stamp{t_sec, t_nsec, RCL_ROS_TIME};

    nav_msgs::msg::Odometry odom_msg;
    odom_msg.header.stamp = stamp;
    odom_msg.header.frame_id = _odom_frame;
    odom_msg.child_frame_id = _base_frame;

    // Position
    odom_msg.pose.pose.position.x = _pose.translation().x();
    odom_msg.pose.pose.position.y = _pose.translation().y();
    odom_msg.pose.pose.position.z = _pose.translation().z();

    // Orientation
    Eigen::Quaterniond quat(_pose.linear());
    odom_msg.pose.pose.orientation.x = quat.x();
    odom_msg.pose.pose.orientation.y = quat.y();
    odom_msg.pose.pose.orientation.z = quat.z();
    odom_msg.pose.pose.orientation.w = quat.w();

    _odom_pub->publish(odom_msg);   
}

void DiffDriverCommon::publish_tf(double time){
    const int32_t t_sec = static_cast<int32_t>(time);
    const uint32_t t_nsec =
        static_cast<uint32_t>((time - static_cast<double>(t_sec)) * 1e9);
    const rclcpp::Time stamp{t_sec, t_nsec, RCL_ROS_TIME};

    geometry_msgs::msg::TransformStamped tf_msg;
    tf_msg.header.stamp = stamp;
    tf_msg.header.frame_id = _odom_frame;
    tf_msg.child_frame_id = _base_frame;

    tf_msg.transform.translation.x = _pose.translation().x();
    tf_msg.transform.translation.y = _pose.translation().y();
    tf_msg.transform.translation.z = _pose.translation().z();

    Eigen::Quaterniond quat(_pose.linear());
    tf_msg.transform.rotation.x = quat.x();
    tf_msg.transform.rotation.y = quat.y();
    tf_msg.transform.rotation.z = quat.z();
    tf_msg.transform.rotation.w = quat.w();

    _tf_broadcaster->sendTransform(tf_msg);
}

}