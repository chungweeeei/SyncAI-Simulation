# Cartographer SLAM 建圖流程

使用 Google Cartographer 在 SyncAI 模擬環境(Isaac Sim + robot01 container)建立 2D occupancy grid map,並輸出 PNG / PGM / pbstream。

## 前置條件

- `syncai-robot01` container 已啟動,Isaac Sim(SyncAI-Omniverse)同時跑著。
- `/clock`、`/robot01/scan`、`/robot01/odom` topic 都有資料。
- LaserScan publisher 衝突已修復(merger 的內建 `/scan` 已 remap 到 `/scan_merged_raw`)。
- Isaac Sim 端 odom publisher 已用 `OnPhysicsStep` trigger(避免 timestamp 重複)。

驗證一行檢查:

```bash
ros2 topic info /robot01/scan -v | grep "Publisher count"   # 應為 1
ros2 topic hz /clock                                         # 持續輸出
```

## Step 0:安裝 Cartographer(只第一次)

進 robot01 container:

```bash
docker exec -it syncai-robot01 bash
sudo apt-get update && sudo apt-get install -y ros-jazzy-cartographer ros-jazzy-cartographer-ros
```

> 永久化要把這兩個套件加進 `robot_ws/Dockerfile` 的 apt-get install 段。

驗證:

```bash
ros2 pkg executables cartographer_ros
```

## Step 1:Lua 設定檔

放在 `data/robot01/cartographer_2d.lua`(host 路徑;mount 進 container 後位於 `/home/ubuntu/data/cartographer_2d.lua`):

```lua
include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "robot01/base_link",
  published_frame = "robot01/odom",
  odom_frame = "robot01/odom",
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
TRAJECTORY_BUILDER_2D.max_range = 25.0
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 5.0
TRAJECTORY_BUILDER_2D.use_imu_data = false
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(0.2)

POSE_GRAPH.constraint_builder.min_score = 0.65
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.7

return options
```

要點:
- `tracking_frame` / `published_frame` / `odom_frame` 都帶 `robot01/` 前綴,因 Nav2/EKF stack 用 namespaced TF。
- `use_imu_data = false`。要開 IMU 的話改成 `true` 並把 `tracking_frame` 改 `robot01/imu_link`。
- `use_odometry = true` 假設 `/robot01/odom` 時間戳嚴格遞增(已修)。

## Step 2:啟動 Cartographer

四個獨立指令 — 建議用 byobu / tmux 開四個 split。每個 terminal 進 container 後都先 source ROS 環境:

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
```

### 2a. cartographer_node(SLAM 主體)

```bash
ros2 run cartographer_ros cartographer_node -configuration_directory /home/ubuntu/data -configuration_basename cartographer_2d.lua --ros-args -p use_sim_time:=true -r __ns:=/robot01 -r scan:=/robot01/scan -r odom:=/robot01/odom
```

> Cartographer 用 gflags,`-configuration_directory` / `-configuration_basename` 必須放在 `--ros-args` **之前**。

### 2b. occupancy_grid_node(把 submaps 轉成 `/map` 給 RViz)

```bash
ros2 run cartographer_ros cartographer_occupancy_grid_node --ros-args -p use_sim_time:=true -p resolution:=0.05 -p publish_period_sec:=1.0 -r __ns:=/robot01
```

### 2c. RViz2(host 端,X11 forwarding)

```bash
rviz2
```

加 displays:

| Display    | Topic                            | QoS                          |
| ---------- | -------------------------------- | ---------------------------- |
| TF         | —                                | —                            |
| Map        | `/robot01/map`                   | Reliable + **Transient Local** |
| LaserScan  | `/robot01/scan`                  | Reliable                     |
| Path       | `/robot01/trajectory_node_list`  | (optional)                   |

Fixed Frame 設 `map`,Global Status 全綠才正常。

### 2d. 遙控

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/robot01/cmd_vel
```

## Step 3:建圖中觀察

驗證 SLAM 狀態:

```bash
ros2 topic hz /robot01/map           # ~1 Hz
ros2 topic list | grep robot01       # 看 cartographer 公開的 topics
ros2 node info /robot01/cartographer_node
```

操作建議:
- 緩慢繞行,避免轉太快(scan-matching 容易飄)。
- 經過容易特徵化的區域(牆角、桌邊)能讓 loop closure 觸發。
- 看 RViz 的 grid 即時長出來,確認沒有「鬼牆」或飄移。

## Step 4:存圖

跑完一圈、車停穩後,**不要關 cartographer_node**,在另一個 terminal 依序執行。

### 4a. 結束當前 trajectory

```bash
ros2 service call /robot01/finish_trajectory cartographer_ros_msgs/srv/FinishTrajectory "{trajectory_id: 0}"
```

> 沒 finish 的話 pbstream 不完整,後續產 grid 會出錯。

### 4b. 存 pbstream(cartographer 原生格式)

```bash
ros2 service call /robot01/write_state cartographer_ros_msgs/srv/WriteState "{filename: '/home/ubuntu/map/cartographer.pbstream', include_unfinished_submaps: true}"
```

成功 `status.code: 0`。檔案出現在 host 的 `./map/cartographer.pbstream`(volume 同步)。

### 4c. 從 pbstream 產 PGM + YAML

```bash
ros2 run cartographer_ros cartographer_pbstream_to_ros_map -pbstream_filename /home/ubuntu/map/cartographer.pbstream -map_filestem /home/ubuntu/map/cartographer_map -resolution 0.05
```

產出 `cartographer_map.pgm` + `cartographer_map.yaml`(含 origin / resolution,可直接餵 Nav2 map_server)。

### 4d. PGM → PNG

```bash
sudo apt-get install -y imagemagick     # 若尚未安裝
convert /home/ubuntu/map/cartographer_map.pgm /home/ubuntu/map/cartographer_map.png
```

最終 host 端產物(`./map/`):

| 檔案 | 用途 |
| --- | --- |
| `cartographer.pbstream` | Cartographer 原生 pose graph,可重新最佳化 |
| `cartographer_map.pgm`  | 灰階 occupancy grid |
| `cartographer_map.yaml` | Nav2 map_server 設定 |
| `cartographer_map.png`  | 給人看 / 文件 / 報告 |

## Step 5:調參優化(提升建圖品質)

當基本流程跑通後,若地圖出現「雙重牆壁」、「鬼牆」、迴圈閉合錯位、長走廊飄移等問題,依下列優先序調整參數。建議:**一次只動 1~2 個參數**,並用同一段 rosbag 反覆測試比較。

### 調參工作流程

1. RViz 訂閱 `/robot01/submap_list` 與 `/robot01/constraint_list`,即時觀察 submap 邊界與迴圈閉合連線。
2. 先 `ros2 bag record /robot01/scan /robot01/odom /tf /tf_static /clock` 錄一段代表性路徑。
3. 重播 bag(`ros2 bag play --clock <bag>`)搭配不同 lua 設定比對。
4. 結束時呼叫 `/finish_trajectory` 讓最後一次全域優化完成,再 `/write_state`。

### 第一優先(影響最大)

#### A. Submap 大小 — `TRAJECTORY_BUILDER_2D.submaps.num_range_data`

預設 90。**最關鍵的參數**。

- 太大 → submap 內部誤差累積、邊緣模糊、雙重牆壁
- 太小 → submap 太多、迴圈閉合機會變少、CPU 高
- 倉儲/室內走廊建議 **35~80**;特徵稀疏時調小

```lua
TRAJECTORY_BUILDER_2D.submaps.num_range_data = 50
```

#### B. Scan Matcher 權重 — `TRAJECTORY_BUILDER_2D.ceres_scan_matcher`

```lua
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.translation_weight = 10.    -- 預設 10
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.rotation_weight = 60.       -- 預設 40
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.occupied_space_weight = 10. -- 預設 1
```

- 信任 odom → 提高 `translation_weight` / `rotation_weight`
- 信任 LiDAR → 提高 `occupied_space_weight`
- SyncAI 沒有 IMU、靠 odom,**`rotation_weight` 拉到 60~80** 防止打滑導致角度漂移

#### C. 迴圈閉合分數 — `POSE_GRAPH.constraint_builder`

預設 `min_score = 0.55` 偏寬鬆,容易誤閉合導致地圖扭曲。

```lua
POSE_GRAPH.constraint_builder.min_score = 0.7                       -- 局部約束
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.75  -- 全域迴圈閉合
```

### 第二優先(影響細節)

#### D. Motion Filter — 抑制重複 scan

目前 `max_angle_radians = math.rad(0.2)` 非常敏感(幾乎不過濾),CPU 較重但細節保留多。

```lua
TRAJECTORY_BUILDER_2D.motion_filter.max_time_seconds = 5.
TRAJECTORY_BUILDER_2D.motion_filter.max_distance_meters = 0.2
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(1.0)
```

慢速精細建圖 → 維持敏感;想減負載 → 放寬到 1°。

#### E. Adaptive Voxel Filter — 過濾入站 scan

```lua
TRAJECTORY_BUILDER_2D.adaptive_voxel_filter.max_length = 0.5
TRAJECTORY_BUILDER_2D.adaptive_voxel_filter.min_num_points = 200
TRAJECTORY_BUILDER_2D.adaptive_voxel_filter.max_range = 25.   -- 對齊 max_range
```

`min_num_points` 太低 → 匹配不穩;太高 → 稀疏環境會丟掉 scan。

#### F. Real-time Correlative Scan Matcher 搜尋窗

已開啟 `use_online_correlative_scan_matching = true`,搭配:

```lua
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.linear_search_window = 0.1
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.angular_search_window = math.rad(20.)
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.translation_delta_cost_weight = 1e-1
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.rotation_delta_cost_weight = 1e-1
```

odom 不準時把搜尋窗開大,但會吃 CPU。

### 第三優先(整體幾何)

#### G. Odometry 權重 — `POSE_GRAPH.optimization_problem`

```lua
POSE_GRAPH.optimization_problem.odometry_translation_weight = 1e5
POSE_GRAPH.optimization_problem.odometry_rotation_weight = 1e5
POSE_GRAPH.optimization_problem.huber_scale = 1e1
```

**輪式打滑明顯時要降低 odom 權重**(例如 1e3),否則優化會被錯誤 odom 拉扯。

#### H. 約束建立頻率與優化頻率

```lua
POSE_GRAPH.constraint_builder.sampling_ratio = 0.4   -- 預設 0.3
POSE_GRAPH.optimize_every_n_nodes = 40               -- 預設 90,建議 < num_range_data
```

建圖期間提高頻率,可更早修正漂移;建圖完再調回預設以省 CPU。

### SyncAI 推薦起手包

針對「沒 IMU + 用 odom + 倉儲場景」,在現有 lua 末段(`return options` 之前)追加:

```lua
-- 縮小 submap,讓迴圈閉合更頻繁修正
TRAJECTORY_BUILDER_2D.submaps.num_range_data = 50

-- 提高 odom 旋轉信任、讓 LiDAR 主導校正
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.rotation_weight = 60.
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.occupied_space_weight = 10.

-- 收緊迴圈閉合分數,避免誤閉合扭曲地圖
POSE_GRAPH.constraint_builder.min_score = 0.7
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.75
POSE_GRAPH.constraint_builder.sampling_ratio = 0.4
POSE_GRAPH.optimize_every_n_nodes = 40
```

### 症狀對應參數速查表

| 症狀                              | 優先調整                                                      |
| --------------------------------- | ------------------------------------------------------------- |
| 雙重牆壁、邊緣模糊                | `submaps.num_range_data` 調小                                 |
| 角度漂移、長走廊歪斜              | `ceres_scan_matcher.rotation_weight` 提高                     |
| 迴圈閉合後地圖扭曲                | `constraint_builder.min_score` 提高(收緊)                  |
| 該閉合卻沒閉合                    | `constraint_builder.min_score` 降低 + `sampling_ratio` 提高   |
| odom 打滑導致地圖被拉壞           | `optimization_problem.odometry_*_weight` 降低                 |
| CPU 過高                          | `motion_filter.max_angle_radians` 放寬;關 `use_online_correlative_scan_matching` |
| 稀疏環境(空曠倉庫)scan 被丟棄  | `adaptive_voxel_filter.min_num_points` 降低                   |

## 常見錯誤

### `Check failed: !FLAGS_configuration_directory.empty()`

`-configuration_directory` flag 被 `--ros-args` 吞掉。**Cartographer 自己的 flag 必須放最前面**,不要放在 `-- ` 後面。

### `map_by_time Check failed: data.time >> std::prev`(timestamp 不嚴格遞增)

時間戳重複或倒退。常見原因:
1. **模擬器重啟導致 sim time 跳回零** → 殺掉 cartographer_node 重跑。
2. **Topic 多重 publisher** → `ros2 topic info /robot01/scan -v` 確認 publisher count = 1。
3. **Isaac Sim odom 用 `OnPlaybackTick`** → render rate 高於 physics rate,連續兩筆 timestamp 相同。改用 `OnPhysicsStep` + `pipeline_stage = GRAPH_PIPELINE_STAGE_ONDEMAND`(見 SyncAI-Omniverse `odom_publisher.py`)。

### Map 在 RViz 顯示 `No messages received`

Map publisher 用 latched QoS,RViz Map display 的 Durability 必須設 `Transient Local`,Reliability 設 `Reliable`。

### `Queue too short for velocity estimation. Queue duration: 0 s`

Cartographer 收到的 odom 時間戳全相同 → 同上「Isaac Sim odom 用 OnPlaybackTick」問題。

## 重新建圖

當前 trajectory finish 後,cartographer_node 不再吃新資料。要重新建圖必須 Ctrl+C 重啟 cartographer_node。
