#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/components/Link.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/Static.hh>
#include <gz/sim/components/Visual.hh>
#include <gz/sim/components/VisualCmd.hh>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/boolean.pb.h>
#include <gz/msgs/stringmsg.pb.h>
#include <gz/msgs/visual.pb.h>
#include <gz/msgs/material.pb.h>

#include <mutex>
#include <string>
#include <cmath>

namespace syncai
{

class AlarmPlugin
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

    if (_sdf->HasElement("link_name"))
      this->linkName_ = _sdf->Get<std::string>("link_name");

    if (_sdf->HasElement("visual_name"))
      this->visualName_ = _sdf->Get<std::string>("visual_name");

    if (_sdf->HasElement("flash_period"))
      this->flashPeriod_ = _sdf->Get<double>("flash_period");

    if (_sdf->HasElement("detection_range"))
      this->detectionRange_ = _sdf->Get<double>("detection_range");

    auto modelName = this->model_.Name(_ecm);
    auto topicPrefix = "/alarm/" + modelName;

    auto serviceTopic = topicPrefix + "/cmd";
    this->node_.Advertise(serviceTopic, &AlarmPlugin::OnCmd, this);
    gzmsg << "[AlarmPlugin] Service advertised: " << serviceTopic << std::endl;

    auto cmdTopic = topicPrefix + "/cmd_topic";
    this->node_.Subscribe(cmdTopic, &AlarmPlugin::OnCmdTopic, this);
    gzmsg << "[AlarmPlugin] Command topic subscribed: " << cmdTopic << std::endl;

    this->statePub_ = this->node_.Advertise<gz::msgs::StringMsg>(
      topicPrefix + "/state");
    gzmsg << "[AlarmPlugin] State topic: " << topicPrefix + "/state" << std::endl;

    gzmsg << "[AlarmPlugin] Configured for model '" << modelName
           << "', detection_range=" << this->detectionRange_ << "m" << std::endl;
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &_info,
    gz::sim::EntityComponentManager &_ecm) override
  {
    if (_info.paused)
      return;

    // Deferred visual entity search on first PreUpdate
    if (!this->visualSearched_)
    {
      this->visualSearched_ = true;
      FindVisualEntity(_ecm);
    }

    double dt = std::chrono::duration<double>(_info.dt).count();

    // Proximity detection: check if any non-static model is within range
    bool proximityTriggered = CheckProximity(_ecm);

    // Combine: active if proximity triggered OR manual command
    bool manualActive;
    {
      std::lock_guard<std::mutex> lock(this->mutex_);
      manualActive = this->manualActive_;
    }
    bool wantActive = proximityTriggered || manualActive;

    // Flash logic
    bool prevLightOn = this->lightOn_;
    if (wantActive)
    {
      this->flashTimer_ += dt;
      if (this->flashTimer_ >= this->flashPeriod_ * 0.5)
      {
        this->flashTimer_ = 0.0;
        this->lightOn_ = !this->lightOn_;
      }
    }
    else
    {
      this->lightOn_ = false;
      this->flashTimer_ = 0.0;
    }

    // Update lens visual color via VisualCmd when state changes
    if (this->visualEntity_ != gz::sim::kNullEntity &&
        this->lightOn_ != prevLightOn)
    {
      gz::msgs::Visual visualMsg;
      auto *mat = visualMsg.mutable_material();
      auto *ambient = mat->mutable_ambient();
      auto *diffuse = mat->mutable_diffuse();
      auto *emissive = mat->mutable_emissive();

      if (this->lightOn_)
      {
        ambient->set_r(1.0f); ambient->set_g(0.0f); ambient->set_b(0.0f); ambient->set_a(1.0f);
        diffuse->set_r(1.0f); diffuse->set_g(0.0f); diffuse->set_b(0.0f); diffuse->set_a(1.0f);
        emissive->set_r(1.0f); emissive->set_g(0.0f); emissive->set_b(0.0f); emissive->set_a(1.0f);
      }
      else
      {
        ambient->set_r(0.4f); ambient->set_g(0.05f); ambient->set_b(0.05f); ambient->set_a(1.0f);
        diffuse->set_r(0.6f); diffuse->set_g(0.1f); diffuse->set_b(0.1f); diffuse->set_a(1.0f);
        emissive->set_r(0.0f); emissive->set_g(0.0f); emissive->set_b(0.0f); emissive->set_a(1.0f);
      }

      auto cmdComp =
        _ecm.Component<gz::sim::components::VisualCmd>(this->visualEntity_);
      if (cmdComp)
      {
        *cmdComp = gz::sim::components::VisualCmd(visualMsg);
      }
      else
      {
        _ecm.CreateComponent(this->visualEntity_,
          gz::sim::components::VisualCmd(visualMsg));
      }
    }

    // Publish state periodically (~2 Hz)
    this->timeSinceLastPub_ += dt;
    if (this->timeSinceLastPub_ >= 0.5)
    {
      this->timeSinceLastPub_ = 0.0;

      gz::msgs::StringMsg stateMsg;
      stateMsg.set_data(wantActive ? "active" : "inactive");
      this->statePub_.Publish(stateMsg);
    }
  }

private:
  /// \brief Check if any non-static model is within detection range
  bool CheckProximity(gz::sim::EntityComponentManager &_ecm)
  {
    auto alarmPose = gz::sim::worldPose(this->model_.Entity(), _ecm);
    auto alarmPos = alarmPose.Pos();
    double rangeSq = this->detectionRange_ * this->detectionRange_;
    auto selfEntity = this->model_.Entity();

    bool detected = false;

    _ecm.Each<gz::sim::components::Model,
              gz::sim::components::Pose,
              gz::sim::components::Static>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Model *,
          const gz::sim::components::Pose *,
          const gz::sim::components::Static *_static) -> bool
      {
        // Skip self and static models
        if (_entity == selfEntity || (_static && _static->Data()))
          return true;

        auto pose = gz::sim::worldPose(_entity, _ecm);
        double distSq = alarmPos.Distance(pose.Pos());
        distSq *= distSq;

        if (alarmPos.Distance(pose.Pos()) <= this->detectionRange_)
        {
          detected = true;
          return false;  // stop iteration
        }
        return true;
      });

    return detected;
  }

  void FindVisualEntity(gz::sim::EntityComponentManager &_ecm)
  {
    auto linkEntity = this->model_.LinkByName(_ecm, this->linkName_);
    if (linkEntity == gz::sim::kNullEntity)
    {
      gzerr << "[AlarmPlugin] Link '" << this->linkName_
             << "' not found" << std::endl;
      return;
    }

    _ecm.Each<gz::sim::components::Name,
              gz::sim::components::Visual,
              gz::sim::components::ParentEntity>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Name *_name,
          const gz::sim::components::Visual *,
          const gz::sim::components::ParentEntity *_parent) -> bool
      {
        if (_parent->Data() == linkEntity &&
            _name->Data() == this->visualName_)
        {
          this->visualEntity_ = _entity;
          gzmsg << "[AlarmPlugin] Found visual '" << this->visualName_
                 << "' (entity " << _entity << ")" << std::endl;
          return false;
        }
        return true;
      });

    if (this->visualEntity_ == gz::sim::kNullEntity)
    {
      gzerr << "[AlarmPlugin] Visual '" << this->visualName_
             << "' not found in link '" << this->linkName_ << "'" << std::endl;
    }
  }

  bool OnCmd(const gz::msgs::Boolean &_req, gz::msgs::Boolean &_rep)
  {
    {
      std::lock_guard<std::mutex> lock(this->mutex_);
      this->manualActive_ = _req.data();
    }
    gzmsg << "[AlarmPlugin] Service command: "
           << (_req.data() ? "TRIGGER" : "RESET") << std::endl;
    _rep.set_data(true);
    return true;
  }

  void OnCmdTopic(const gz::msgs::Boolean &_msg)
  {
    {
      std::lock_guard<std::mutex> lock(this->mutex_);
      this->manualActive_ = _msg.data();
    }
    gzmsg << "[AlarmPlugin] Topic command: "
           << (_msg.data() ? "TRIGGER" : "RESET") << std::endl;
  }

  gz::sim::Model model_{gz::sim::kNullEntity};
  gz::sim::Entity visualEntity_{gz::sim::kNullEntity};

  gz::transport::Node node_;
  gz::transport::Node::Publisher statePub_;

  std::string linkName_{"base_link"};
  std::string visualName_{"lens_visual"};
  double flashPeriod_{1.0};
  double detectionRange_{3.0};   // meters

  bool visualSearched_{false};
  bool manualActive_{false};
  bool lightOn_{false};
  double flashTimer_{0.0};
  double timeSinceLastPub_{0.0};

  std::mutex mutex_;
};

}  // namespace syncai

GZ_ADD_PLUGIN(
  syncai::AlarmPlugin,
  gz::sim::System,
  syncai::AlarmPlugin::ISystemConfigure,
  syncai::AlarmPlugin::ISystemPreUpdate)
