FROM ubuntu:24.04

# Install pre-requisites
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    build-essential \
    cmake \
    git \
    wget \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    > /etc/apt/sources.list.d/ros2.list

ENV DEBIAN_FRONTEND=noninteractive

# Install ROS 2 Jazzy + Navigation2 + dependencies
RUN apt-get update && apt-get install -y \
    ros-jazzy-ros-base \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-slam-toolbox \
    ros-jazzy-tf2-ros \
    ros-jazzy-tf2-tools \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rosidl-default-generators \
    ros-jazzy-rosidl-default-runtime \
    ros-jazzy-std-msgs \
    ros-jazzy-geometry-msgs \
    ros-jazzy-sensor-msgs \
    ros-jazzy-rviz2 \
    python3-colcon-common-extensions \
    python3-rosdep \
    byobu \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Initialize rosdep
RUN rosdep init || true && rosdep update --rosdistro jazzy

# Install Python dependencies (for syncai_robot_api)
RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install --break-system-packages \
    structlog \
    fastapi \
    uvicorn \
    confluent-kafka \
    requests \
    temporalio

# Dev tools
RUN apt-get update && apt-get install -y \
    gdb \
    clang-format \
    python3-pytest \
    python3-flake8 \
    bash-completion \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Setup ubuntu user with sudo
RUN echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER ubuntu
WORKDIR /home/ubuntu

# Auto-source ROS 2 and workspace in every shell
RUN echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc && \
    echo '[ -f ~/robot_ws/install/setup.bash ] && source ~/robot_ws/install/setup.bash' >> ~/.bashrc && \
    echo 'eval "$(register-python-argcomplete3 ros2)"' >> ~/.bashrc && \
    echo 'eval "$(register-python-argcomplete3 colcon)"' >> ~/.bashrc

ENV SYNCAI_DATA_DIR=/home/ubuntu/data
