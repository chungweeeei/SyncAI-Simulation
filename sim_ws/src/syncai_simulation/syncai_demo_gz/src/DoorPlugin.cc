#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Joint.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/components/Joint.hh>
#include <gz/sim/components/JointPosition.hh>
#include <gz/sim/components/JointPositionReset.hh>
#include <gz/sim/components/Name.hh>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/boolean.pb.h>
#include <gz/msgs/stringmsg.pb.h>

#include <mutex>
#include <string>
#include <cmath>
#include <vector>

namespace syncai
{

class DoorPlugin
  : public gz::sim::System,
    public gz::sim::ISystemConfigure,
    public gz::sim::ISystemPreUpdate
{
public:
  void Configure(
    const gz::sim::Entity &_entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &_ecm,
    gz::sim::EventManager & /*_eventMgr*/) override
  {
    this->model_ = gz::sim::Model(_entity);

    // Read SDF parameters
    if (_sdf->HasElement("left_joint"))
      this->leftJointName_ = _sdf->Get<std::string>("left_joint");

    if (_sdf->HasElement("right_joint"))
      this->rightJointName_ = _sdf->Get<std::string>("right_joint");

    if (_sdf->HasElement("slide_distance"))
      this->slideDistance_ = _sdf->Get<double>("slide_distance");

    if (_sdf->HasElement("speed"))
      this->speed_ = _sdf->Get<double>("speed");

    // Resolve model-scoped topic name
    auto modelName = this->model_.Name(_ecm);
    auto topicPrefix = "/door/" + modelName;

    // Advertise service: /door/<model_name>/cmd
    auto serviceTopic = topicPrefix + "/cmd";
    this->node_.Advertise(serviceTopic, &DoorPlugin::OnCmd, this);
    gzmsg << "[DoorPlugin] Service advertised: " << serviceTopic << std::endl;

    // Subscribe to command topic (bridgeable from ROS2)
    auto cmdTopic = topicPrefix + "/cmd_topic";
    this->node_.Subscribe(cmdTopic, &DoorPlugin::OnCmdTopic, this);
    gzmsg << "[DoorPlugin] Command topic subscribed: " << cmdTopic << std::endl;

    // Advertise state topic
    this->statePub_ = this->node_.Advertise<gz::msgs::StringMsg>(
      topicPrefix + "/state");
    gzmsg << "[DoorPlugin] State topic: " << topicPrefix + "/state" << std::endl;

    // Find joint entities
    this->leftJointEntity_ = this->model_.JointByName(_ecm, this->leftJointName_);
    this->rightJointEntity_ = this->model_.JointByName(_ecm, this->rightJointName_);

    if (this->leftJointEntity_ == gz::sim::kNullEntity)
    {
      gzerr << "[DoorPlugin] Left joint '" << this->leftJointName_
             << "' not found" << std::endl;
      return;
    }
    if (this->rightJointEntity_ == gz::sim::kNullEntity)
    {
      gzerr << "[DoorPlugin] Right joint '" << this->rightJointName_
             << "' not found" << std::endl;
      return;
    }

    // Ensure JointPosition components exist
    for (auto entity : {this->leftJointEntity_, this->rightJointEntity_})
    {
      if (!_ecm.Component<gz::sim::components::JointPosition>(entity))
      {
        _ecm.CreateComponent(entity,
          gz::sim::components::JointPosition({0.0}));
      }
    }

    gzmsg << "[DoorPlugin] Configured sliding door for model '" << modelName
           << "'" << std::endl;
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &_info,
    gz::sim::EntityComponentManager &_ecm) override
  {
    if (_info.paused ||
        this->leftJointEntity_ == gz::sim::kNullEntity ||
        this->rightJointEntity_ == gz::sim::kNullEntity)
      return;

    bool wantOpen;
    {
      std::lock_guard<std::mutex> lock(this->mutex_);
      wantOpen = this->targetOpen_;
    }

    double dt = std::chrono::duration<double>(_info.dt).count();
    double step = this->speed_ * dt;

    // Left panel slides in negative Y, right panel slides in positive Y
    // Target: slideDistance_ when open, 0 when closed
    double targetLeft = wantOpen ? -this->slideDistance_ : 0.0;
    double targetRight = wantOpen ? this->slideDistance_ : 0.0;

    double newLeft = MoveToward(
      GetJointPos(_ecm, this->leftJointEntity_), targetLeft, step);
    double newRight = MoveToward(
      GetJointPos(_ecm, this->rightJointEntity_), targetRight, step);

    SetJointPos(_ecm, this->leftJointEntity_, newLeft);
    SetJointPos(_ecm, this->rightJointEntity_, newRight);

    // Publish state periodically (~2 Hz)
    this->timeSinceLastPub_ += dt;
    if (this->timeSinceLastPub_ >= 0.5)
    {
      this->timeSinceLastPub_ = 0.0;

      bool atTarget =
        std::abs(newLeft - targetLeft) < 0.005 &&
        std::abs(newRight - targetRight) < 0.005;

      gz::msgs::StringMsg stateMsg;
      if (atTarget)
        stateMsg.set_data(wantOpen ? "open" : "closed");
      else
        stateMsg.set_data(wantOpen ? "opening" : "closing");

      this->statePub_.Publish(stateMsg);
    }
  }

private:
  static double GetJointPos(
    gz::sim::EntityComponentManager &_ecm, gz::sim::Entity _joint)
  {
    auto comp = _ecm.Component<gz::sim::components::JointPosition>(_joint);
    if (!comp || comp->Data().empty())
      return 0.0;
    return comp->Data()[0];
  }

  static void SetJointPos(
    gz::sim::EntityComponentManager &_ecm, gz::sim::Entity _joint, double _pos)
  {
    auto comp =
      _ecm.Component<gz::sim::components::JointPositionReset>(_joint);
    if (comp)
      comp->Data() = {_pos};
    else
      _ecm.CreateComponent(_joint,
        gz::sim::components::JointPositionReset({_pos}));
  }

  static double MoveToward(double current, double target, double step)
  {
    double diff = target - current;
    if (std::abs(diff) <= step)
      return target;
    return current + (diff > 0 ? step : -step);
  }

  bool OnCmd(const gz::msgs::Boolean &_req, gz::msgs::Boolean &_rep)
  {
    {
      std::lock_guard<std::mutex> lock(this->mutex_);
      this->targetOpen_ = _req.data();
    }
    gzmsg << "[DoorPlugin] Service command: "
           << (_req.data() ? "OPEN" : "CLOSE") << std::endl;
    _rep.set_data(true);
    return true;
  }

  void OnCmdTopic(const gz::msgs::Boolean &_msg)
  {
    {
      std::lock_guard<std::mutex> lock(this->mutex_);
      this->targetOpen_ = _msg.data();
    }
    gzmsg << "[DoorPlugin] Topic command: "
           << (_msg.data() ? "OPEN" : "CLOSE") << std::endl;
  }

  gz::sim::Model model_{gz::sim::kNullEntity};
  gz::sim::Entity leftJointEntity_{gz::sim::kNullEntity};
  gz::sim::Entity rightJointEntity_{gz::sim::kNullEntity};

  gz::transport::Node node_;
  gz::transport::Node::Publisher statePub_;

  std::string leftJointName_{"left_door_joint"};
  std::string rightJointName_{"right_door_joint"};
  double slideDistance_{0.5};   // meters each panel slides
  double speed_{0.5};           // m/s

  bool targetOpen_{false};
  double timeSinceLastPub_{0.0};

  std::mutex mutex_;
};

}  // namespace syncai

GZ_ADD_PLUGIN(
  syncai::DoorPlugin,
  gz::sim::System,
  syncai::DoorPlugin::ISystemConfigure,
  syncai::DoorPlugin::ISystemPreUpdate)
