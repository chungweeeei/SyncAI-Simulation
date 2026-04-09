FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    build-essential \
    golang-go \
    byobu \
    && rm -rf /var/lib/apt/lists/*

# Install ROS 2 Jazzy (for CycloneDDS libs only)
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    > /etc/apt/sources.list.d/ros2.list

RUN apt-get update && apt-get install -y \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-cyclonedds \
    ros-jazzy-iceoryx-binding-c \
    && rm -rf /var/lib/apt/lists/*

ENV LD_LIBRARY_PATH=/opt/ros/jazzy/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH

RUN echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER ubuntu
WORKDIR /app

ENTRYPOINT ["bash", "-c", "source /opt/ros/jazzy/setup.bash && exec \"$@\"", "--"]
CMD ["bash"]
