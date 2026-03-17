#ifndef SYNCAI_AMR_SIM_COMMON__DIFF_DRIVE_COMMON_HPP
#define SYNCAI_AMR_SIM_COMMON__DIFF_DRIVE_COMMON_HPP

#include <rclcpp/rclcpp.hpp>
#include <Eigen/Geometry>
#include <tf2_ros/transform_broadcaster.h>

#include <geometry_msgs/msg/twist.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <nav_msgs/msg/odometry.hpp>

namespace syncai_amr_sim_common
{
class DiffDriverCommon
{
public:
    
    struct UpdateResult{
        double linear_vel = 0.0; // m/s (forward velocity)
        double angular_vel = 0.0; // rad/s (angular velocity)
    };

    DiffDriverCommon();
    ~DiffDriverCommon() = default;

    // setting function
    void set_model_name(const std::string &model_name);
    std::string model_name() const;
    rclcpp::Logger logger() const;

    // read parameters from SDF file
    template<typename SdfPtrT>
    void read_sdf(SdfPtrT& sdf);

    // initialized ROS2 node
    void init_ros_node(rclcpp::Node::SharedPtr node);

    // update function
    UpdateResult update(const Eigen::Isometry3d& pose, double time);

private:
    rclcpp::Node::SharedPtr _ros_node;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr _cmd_vel_sub;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr _odom_pub;
    std::shared_ptr<tf2_ros::TransformBroadcaster> _tf_broadcaster;

    // state variables
    std::string _model_name;
    Eigen::Isometry3d _pose;     // current pose
    Eigen::Isometry3d _last_pose; // previous pose
    double _last_update_time = 0.0;
    bool _initialized = false;

    // current velocity command
    double _cmd_linear_vel = 0.0;
    double _cmd_angular_vel = 0.0;

    // actually velocity
    double _actual_linear_vel = 0.0;
    double _actual_angular_vel = 0.0;

    // robot parameters
    double _wheel_radius = 0.1;
    double _wheel_separation = 0.5;
    double _max_linear_vel = 1.0;
    double _max_angular_vel = 2.0;
    double _max_linear_accel = 0.5;
    double _max_angular_accel = 1.0;

    // TF frame names
    std::string _odom_frame = "odom";
    std::string _base_frame = "base_link";

    // publish rate
    double _odom_publish_rate = 50.0; 
    double _last_odom_publish_time = 0.0;

    // callback functions
    void cmd_vel_callback(const geometry_msgs::msg::Twist::SharedPtr msg);
    void publish_odometry(double time);
    void publish_tf(double time);
    double compute_yaw(const Eigen::Isometry3d& pose) const;

    double apply_acceleration_limit(double current, double target, 
                                     double max_accel, double dt) const;
};

template<typename SdfPtrT>
void DiffDriverCommon::read_sdf(SdfPtrT& sdf)
{
  auto get_param = [&](const std::string& name, auto& value) {
    if (sdf->HasElement(name)) {
      value = sdf->template Get<std::remove_reference_t<decltype(value)>>(name);
      RCLCPP_INFO(logger(), "Setting %s to: %s", 
                  name.c_str(), std::to_string(value).c_str());
    }
  };

  get_param("wheel_radius", _wheel_radius);
  get_param("wheel_separation", _wheel_separation);
  get_param("max_linear_vel", _max_linear_vel);
  get_param("max_angular_vel", _max_angular_vel);
  get_param("max_linear_accel", _max_linear_accel);
  get_param("max_angular_accel", _max_angular_accel);
  get_param("odom_publish_rate", _odom_publish_rate);

  if (sdf->HasElement("odom_frame"))
    _odom_frame = sdf->template Get<std::string>("odom_frame");
  if (sdf->HasElement("base_frame"))
    _base_frame = sdf->template Get<std::string>("base_frame");

  RCLCPP_INFO(logger(), "DiffDriver params: wheel_r=%.3f, wheel_sep=%.3f, "
              "max_v=%.2f, max_w=%.2f",
              _wheel_radius, _wheel_separation, 
              _max_linear_vel, _max_angular_vel);
}


} // namespace syncai_amr_sim_common
#endif