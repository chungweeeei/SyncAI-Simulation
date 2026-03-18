#ifndef SYNCAI_ROBOT_SIM_COMMON_DIFF_DRIVER_COMMON_HPP
#define SYNCAI_ROBOT_SIM_COMMON_DIFF_DRIVER_COMMON_HPP

#include <mutex>
#include <string>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <tf2_ros/transform_broadcaster.h>

#include <Eigen/Geometry>

namespace syncai_robot_sim_common
{

class DiffDriverCommon
{
public:
    struct Config
    {
        double wheel_separation = 0.36;
        double wheel_radius = 0.1;
        double max_linear_velocity = 1.0;
        double max_angular_velocity = 2.0;

        std::string cmd_vel_topic = "cmd_vel";
        std::string odom_topic = "odom";
        std::string odom_frame_id = "odom";
        std::string base_frame_id = "base_link";

        double odom_publish_rate = 50.0; // Hz
    };

    struct VelocityCommand
    {
        double linear_x = 0.0;
        double angular_z = 0.0;
    };

    DiffDriverCommon();

    rclcpp::Logger logger() const;

    void set_model_name(const std::string &model_name);
    std::string model_name() const;

    // Read configuration from SDF element
    template<typename SdfPtrT>
    void read_sdf(SdfPtrT& sdf);

    // Initialize ROS 2 node, subscribers, publishers
    void init_ros_node(const rclcpp::Node::SharedPtr node);

    // Get the latest velocity command (thread-safe)
    VelocityCommand get_velocity_command() const;

    void update_odometry(const Eigen::Isometry3d& pose, double time);

private:
    void cmd_vel_callback(const geometry_msgs::msg::Twist::SharedPtr msg);

    Config _config;
    std::string _model_name;

    rclcpp::Node::SharedPtr _ros_node;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr _cmd_vel_sub;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr _odom_pub;
    std::shared_ptr<tf2_ros::TransformBroadcaster> _tf2_broadcaster;

    mutable std::mutex _cmd_vel_mutex;
    VelocityCommand _latest_cmd;

    double _last_odom_pub_time = 0.0;
    bool _initialized_pose = false;
    Eigen::Isometry3d _old_pose = Eigen::Isometry3d::Identity();
    double _last_update_time = 0.0;
};

// ---------- SDF reader (template, defined in header) ----------
template<typename SdfPtrT, typename ValueT>
bool get_sdf_element(
  SdfPtrT& _sdf,
  const std::string& _element_name,
  ValueT& _val)
{
  if (!_sdf->HasElement(_element_name))
  {
    return false;
  }
  _val = _sdf->template Get<ValueT>(_element_name);
  return true;
};

template<typename SdfPtrT>
void DiffDriverCommon::read_sdf(SdfPtrT& sdf)
{
  get_sdf_element(sdf, "wheel_separation", _config.wheel_separation);
  get_sdf_element(sdf, "wheel_radius", _config.wheel_radius);
  get_sdf_element(sdf, "max_linear_velocity", _config.max_linear_velocity);
  get_sdf_element(sdf, "max_angular_velocity", _config.max_angular_velocity);
  get_sdf_element(sdf, "cmd_vel_topic", _config.cmd_vel_topic);
  get_sdf_element(sdf, "odom_topic", _config.odom_topic);
  get_sdf_element(sdf, "odom_frame_id", _config.odom_frame_id);
  get_sdf_element(sdf, "base_frame_id", _config.base_frame_id);
  get_sdf_element(sdf, "odom_publish_rate", _config.odom_publish_rate);

  RCLCPP_INFO(logger(),
    "DiffDriver [%s]: wheel_sep=%.3f, wheel_rad=%.3f, max_lin=%.2f, max_ang=%.2f",
    _model_name.c_str(),
    _config.wheel_separation, _config.wheel_radius,
    _config.max_linear_velocity, _config.max_angular_velocity);
};
}
#endif