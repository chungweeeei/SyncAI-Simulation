#include <chrono>
#include <cctype>
#include <iostream>
#include <memory>
#include <string>

#include <gz/plugin/Register.hh>

#include <gz/math/Pose3.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/System.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/components/JointVelocityCmd.hh>
#include <gz/sim/components/Pose.hh>

#include <rclcpp/rclcpp.hpp>

#include <Eigen/Geometry>
#include <sdf/Element.hh>

#include "syncai_robot_sim_common/diff_driver_common.hpp"


namespace syncai_robot_sim_gz_plugins
{
class DiffDrivePlugin
  : public gz::sim::System,
    public gz::sim::ISystemConfigure,
    public gz::sim::ISystemPreUpdate
{
public:
  void Configure(
    const gz::sim::Entity& entity,
    const std::shared_ptr<const sdf::Element>& sdf,
    gz::sim::EntityComponentManager& ecm,
    gz::sim::EventManager&) override
  {
    this->model_entity_ = entity;
    this->model_ = gz::sim::Model(entity);

    if (!this->model_.Valid(ecm))
    {
      std::cerr << "[DiffDrivePlugin] Invalid model entity" << std::endl;
      return;
    }

    this->model_name_ = this->model_.Name(ecm);
    this->common->set_model_name(this->model_name_);
    this->common->read_sdf(sdf);

    if (sdf->HasElement("left_joint"))
      this->left_joint_name_ = sdf->Get<std::string>("left_joint");

    if (sdf->HasElement("right_joint"))
      this->right_joint_name_ = sdf->Get<std::string>("right_joint");

    if (sdf->HasElement("wheel_separation"))
      this->wheel_separation_ = sdf->Get<double>("wheel_separation");

    if (sdf->HasElement("wheel_radius"))
      this->wheel_radius_ = sdf->Get<double>("wheel_radius");

    this->left_joint_entity_ = this->model_.JointByName(ecm, this->left_joint_name_);
    this->right_joint_entity_ = this->model_.JointByName(ecm, this->right_joint_name_);

    if (this->left_joint_entity_ == gz::sim::kNullEntity ||
        this->right_joint_entity_ == gz::sim::kNullEntity)
    {
      std::cerr << "[DiffDrivePlugin] Failed to find wheel joints: left=["
                << this->left_joint_name_ << "] right=["
                << this->right_joint_name_ << "]" << std::endl;
      return;
    }

    enableComponent<gz::sim::components::Pose>(ecm, entity);
  }
}

}