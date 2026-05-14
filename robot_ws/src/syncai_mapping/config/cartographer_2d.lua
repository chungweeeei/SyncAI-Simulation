include "map_builder.lua"
include "trajectory_builder.lua"

-- <robot_namespace> placeholder is replaced at launch time by
-- syncai_mapping/launch/cartographer_launch.py before being handed to
-- cartographer_node. Frames must match the namespaced TF tree (e.g.
-- robot01/base_link, robot01/odom).
--
-- Isaac Sim already publishes <ns>/odom -> <ns>/base_link at 60 Hz, so
-- provide_odom_frame must be false and published_frame must be the odom
-- frame; otherwise Cartographer would re-publish the same edge and fight
-- the simulator over base_link's pose. Cartographer's responsibility is
-- map -> <ns>/odom only.
options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "<robot_namespace>/base_link",
  published_frame = "<robot_namespace>/odom",
  odom_frame = "<robot_namespace>/odom",
  provide_odom_frame = false,
  publish_frame_projected_to_2d = true,
  use_pose_extrapolator = true,
  use_odometry = true,
  use_nav_sat = false,
  use_landmarks = false,
  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,
  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,
  rangefinder_sampling_ratio = 1.0,
  odometry_sampling_ratio = 1.0,
  fixed_frame_pose_sampling_ratio = 1.0,
  imu_sampling_ratio = 1.0,
  landmarks_sampling_ratio = 1.0,
}

MAP_BUILDER.use_trajectory_builder_2d = true

TRAJECTORY_BUILDER_2D.min_range = 0.12
-- Aligned with pointcloud_to_laserscan.range_max in
-- syncai_bringup/config/laser_scan_merger_params.yaml. Beams beyond 10 m
-- are clipped to +inf upstream so keeping max_range higher here would just
-- waste a missing_data_ray_length insertion on every scan.
TRAJECTORY_BUILDER_2D.max_range = 25.0
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 5.0
TRAJECTORY_BUILDER_2D.use_imu_data = false
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(0.2)

POSE_GRAPH.constraint_builder.min_score = 0.65
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.7

return options
