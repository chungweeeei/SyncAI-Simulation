#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/components/Link.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/sim/components/Visual.hh>
#include <gz/sim/components/VisualCmd.hh>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/boolean.pb.h>
#include <gz/msgs/visual.pb.h>
#include <gz/msgs/material.pb.h>

#include <mutex>
#include <string>

namespace syncai
{

class RobotLedPlugin
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

    auto modelName = this->model_.Name(_ecm);
    auto cmdTopic = "/" + modelName + "/alert";
    this->node_.Subscribe(cmdTopic, &RobotLedPlugin::OnAlert, this);
    gzmsg << "[RobotLedPlugin] Subscribed to: " << cmdTopic << std::endl;
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &_info,
    gz::sim::EntityComponentManager &_ecm) override
  {
    if (_info.paused)
      return;

    if (!this->visualSearched_)
    {
      this->visualSearched_ = true;
      FindVisualEntity(_ecm);
    }

    double dt = std::chrono::duration<double>(_info.dt).count();

    bool active;
    {
      std::lock_guard<std::mutex> lock(this->mutex_);
      active = this->active_;
    }

    bool prevLightOn = this->lightOn_;
    if (active)
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
        // Amber/orange
        ambient->set_r(1.0f); ambient->set_g(0.6f); ambient->set_b(0.0f); ambient->set_a(1.0f);
        diffuse->set_r(1.0f); diffuse->set_g(0.6f); diffuse->set_b(0.0f); diffuse->set_a(1.0f);
        emissive->set_r(1.0f); emissive->set_g(0.6f); emissive->set_b(0.0f); emissive->set_a(1.0f);
      }
      else
      {
        // Dark gray (off)
        ambient->set_r(0.2f); ambient->set_g(0.2f); ambient->set_b(0.2f); ambient->set_a(1.0f);
        diffuse->set_r(0.2f); diffuse->set_g(0.2f); diffuse->set_b(0.2f); diffuse->set_a(1.0f);
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
  }

private:
  void FindVisualEntity(gz::sim::EntityComponentManager &_ecm)
  {
    auto linkEntity = this->model_.LinkByName(_ecm, this->linkName_);
    if (linkEntity == gz::sim::kNullEntity)
    {
      gzerr << "[RobotLedPlugin] Link '" << this->linkName_
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
          gzmsg << "[RobotLedPlugin] Found visual '" << this->visualName_
                 << "' (entity " << _entity << ")" << std::endl;
          return false;
        }
        return true;
      });

    if (this->visualEntity_ == gz::sim::kNullEntity)
    {
      gzerr << "[RobotLedPlugin] Visual '" << this->visualName_
             << "' not found in link '" << this->linkName_ << "'" << std::endl;
    }
  }

  void OnAlert(const gz::msgs::Boolean &_msg)
  {
    std::lock_guard<std::mutex> lock(this->mutex_);
    this->active_ = _msg.data();
    gzmsg << "[RobotLedPlugin] Alert: "
           << (_msg.data() ? "ON" : "OFF") << std::endl;
  }

  gz::sim::Model model_{gz::sim::kNullEntity};
  gz::sim::Entity visualEntity_{gz::sim::kNullEntity};

  gz::transport::Node node_;

  std::string linkName_{"base_link"};
  std::string visualName_{"led_strip_visual"};
  double flashPeriod_{0.6};

  bool visualSearched_{false};
  bool active_{false};
  bool lightOn_{false};
  double flashTimer_{0.0};

  std::mutex mutex_;
};

}  // namespace syncai

GZ_ADD_PLUGIN(
  syncai::RobotLedPlugin,
  gz::sim::System,
  syncai::RobotLedPlugin::ISystemConfigure,
  syncai::RobotLedPlugin::ISystemPreUpdate)
