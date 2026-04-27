FROM ubuntu:24.04

# Install pre-requisites
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    > /etc/apt/sources.list.d/ros2.list

ENV DEBIAN_FRONTEND=noninteractive

# Install ROS 2 and dependencies (Isaac Sim is run on host, not inside this container)
RUN apt-get update && apt-get install -y \
    ros-jazzy-ros-base \
    ros-jazzy-tf2-ros \
    ros-jazzy-teleop-twist-keyboard \
    ros-jazzy-rmw-cyclonedds-cpp \
    libeigen3-dev \
    python3-colcon-common-extensions \
    python3-rosdep \
    mesa-utils \
    libgl1-mesa-dri \
    libgl1 \
    byobu \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Initialized ros dep
RUN rosdep init || true && rosdep update --rosdistro jazzy

# Install Python dependencies
RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install --break-system-packages \
    structlog \
    fastapi \
    uvicorn \
    websockets \ 
    confluent-kafka \
    pymodbus==3.12.1

COPY scripts/entrypoint.sh /home/ubuntu/entrypoint.sh
RUN chmod +x /home/ubuntu/entrypoint.sh

RUN echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

ARG HOST_UID=1000
ARG HOST_GID=1000
RUN groupmod -g ${HOST_GID} ubuntu && \
    usermod -u ${HOST_UID} -g ${HOST_GID} ubuntu && \
    chown -R ${HOST_UID}:${HOST_GID} /home/ubuntu

USER ubuntu

RUN echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc && \
    echo '[ -f ~/sim_ws/install/setup.bash ] && source ~/sim_ws/install/setup.bash' >> ~/.bashrc
WORKDIR /home/ubuntu/sim_ws

ENTRYPOINT [ "/home/ubuntu/entrypoint.sh" ]
CMD ["bash"]