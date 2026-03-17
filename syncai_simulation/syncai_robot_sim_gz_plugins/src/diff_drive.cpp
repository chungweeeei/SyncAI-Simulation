#include <gz/plugin/Register.hh>
#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/LinearVelocityCmd.hh>
#include <gz/sim/components/AngularVelocityCmd.hh>

#include <rclcpp/rclcpp.hpp>
#include <syncai_robot_sim_common/diff_drive_common.hpp>

using namespace gz::sim;

class GZ_SIM_VISIBLE DiffDrivePlugin
  : public System,
    public ISystemConfigure,
    public ISystemPreUpdate
{
public:
  DiffDrivePlugin()
    : _diff_drive(std::make_unique<syncai_amr_sim_common::DiffDriverCommon>())
  {}

  void Configure(const Entity& entity,
    const std::shared_ptr<const sdf::Element>& sdf,
    EntityComponentManager& ecm, EventManager&) override
  {
    _entity = entity;
    auto model = Model(entity);
    std::string model_name = model.Name(ecm);

    _diff_drive->set_model_name(model_name);
    _diff_drive->read_sdf(sdf);

    char const** argv = NULL;
    if (!rclcpp::ok())
      rclcpp::init(0, argv);

    std::string node_name = "diff_drive_" + model_name;
    _ros_node = std::make_shared<rclcpp::Node>(node_name);
    _diff_drive->init_ros_node(_ros_node);

    enableComponent<components::Pose>(ecm, entity);
  }

  void PreUpdate(const UpdateInfo& info, EntityComponentManager& ecm) override
  {
    rclcpp::spin_some(_ros_node);

    if (info.paused)
      return;

    double time =
      std::chrono::duration_cast<std::chrono::nanoseconds>(info.simTime).count()
      * 1e-9;

    // 從 Gazebo 取得目前 pose
    auto pose_comp = ecm.Component<components::Pose>(_entity);
    if (!pose_comp) return;

    Eigen::Isometry3d pose;
    const auto& gz_pose = pose_comp->Data();
    pose.translation() = Eigen::Vector3d(
      gz_pose.Pos().X(), gz_pose.Pos().Y(), gz_pose.Pos().Z());
    pose.linear() = Eigen::Quaterniond(
      gz_pose.Rot().W(), gz_pose.Rot().X(),
      gz_pose.Rot().Y(), gz_pose.Rot().Z()).toRotationMatrix();

    // 呼叫 common 計算控制指令
    auto result = _diff_drive->update(pose, time);

    // 寫入速度指令到 Gazebo
    ecm.SetComponentData<components::LinearVelocityCmd>(
      _entity, gz::math::Vector3d(result.linear_vel, 0, 0));
    ecm.SetComponentData<components::AngularVelocityCmd>(
      _entity, gz::math::Vector3d(0, 0, result.angular_vel));
  }

private:
  std::unique_ptr<syncai_amr_sim_common::DiffDriverCommon> _diff_drive;
  rclcpp::Node::SharedPtr _ros_node;
  Entity _entity;
};

GZ_ADD_PLUGIN(
  DiffDrivePlugin, System,
  DiffDrivePlugin::ISystemConfigure,
  DiffDrivePlugin::ISystemPreUpdate)

GZ_ADD_PLUGIN_ALIAS(DiffDrivePlugin, "diff_drive")