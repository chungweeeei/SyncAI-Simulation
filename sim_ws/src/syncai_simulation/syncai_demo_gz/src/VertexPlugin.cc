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
#include <gz/msgs/visual.pb.h>
#include <gz/msgs/material.pb.h>

#include <string>
#include <cmath>

namespace syncai
{

class VertexPlugin
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

    if (_sdf->HasElement("detection_range"))
      this->detectionRange_ = _sdf->Get<double>("detection_range");

    auto modelName = this->model_.Name(_ecm);
    gzmsg << "[VertexPlugin] Configured for model '" << modelName
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

    // 2D proximity detection (XY only)
    bool occupied = CheckProximity2D(_ecm);

    // Update visual color when state changes
    if (this->visualEntity_ != gz::sim::kNullEntity &&
        occupied != this->occupied_)
    {
      this->occupied_ = occupied;

      gz::msgs::Visual visualMsg;
      auto *mat = visualMsg.mutable_material();
      auto *ambient = mat->mutable_ambient();
      auto *diffuse = mat->mutable_diffuse();
      auto *emissive = mat->mutable_emissive();

      if (occupied)
      {
        // Green when occupied
        ambient->set_r(0.0f); ambient->set_g(1.0f); ambient->set_b(0.0f); ambient->set_a(1.0f);
        diffuse->set_r(0.0f); diffuse->set_g(1.0f); diffuse->set_b(0.0f); diffuse->set_a(1.0f);
        emissive->set_r(0.0f); emissive->set_g(0.8f); emissive->set_b(0.0f); emissive->set_a(1.0f);
      }
      else
      {
        // Grey when idle
        ambient->set_r(0.3f); ambient->set_g(0.3f); ambient->set_b(0.3f); ambient->set_a(1.0f);
        diffuse->set_r(0.4f); diffuse->set_g(0.4f); diffuse->set_b(0.4f); diffuse->set_a(1.0f);
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
  /// \brief Check if any non-static model is within range (2D: XY only)
  bool CheckProximity2D(gz::sim::EntityComponentManager &_ecm)
  {
    auto vertexPose = gz::sim::worldPose(this->model_.Entity(), _ecm);
    double vx = vertexPose.Pos().X();
    double vy = vertexPose.Pos().Y();
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
        if (_entity == selfEntity || (_static && _static->Data()))
          return true;

        auto pose = gz::sim::worldPose(_entity, _ecm);
        double dx = vx - pose.Pos().X();
        double dy = vy - pose.Pos().Y();
        double dist2D = std::sqrt(dx * dx + dy * dy);

        if (dist2D <= this->detectionRange_)
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
      gzerr << "[VertexPlugin] Link '" << this->linkName_
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
          gzmsg << "[VertexPlugin] Found visual '" << this->visualName_
                 << "' (entity " << _entity << ")" << std::endl;
          return false;
        }
        return true;
      });

    if (this->visualEntity_ == gz::sim::kNullEntity)
    {
      gzerr << "[VertexPlugin] Visual '" << this->visualName_
             << "' not found in link '" << this->linkName_ << "'" << std::endl;
    }
  }

  gz::sim::Model model_{gz::sim::kNullEntity};
  gz::sim::Entity visualEntity_{gz::sim::kNullEntity};

  std::string linkName_{"base_link"};
  std::string visualName_{"marker_visual"};
  double detectionRange_{0.5};   // meters

  bool visualSearched_{false};
  bool occupied_{false};
};

}  // namespace syncai

GZ_ADD_PLUGIN(
  syncai::VertexPlugin,
  gz::sim::System,
  syncai::VertexPlugin::ISystemConfigure,
  syncai::VertexPlugin::ISystemPreUpdate)
