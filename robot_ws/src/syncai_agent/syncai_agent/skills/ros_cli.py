import subprocess


def _run_ros_cmd(cmd: list[str], timeout: float = 30.0) -> dict:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": f"Command timed out after {timeout}s"}


def ros2_topic_list() -> dict:
    return _run_ros_cmd(["ros2", "topic", "list"])


def ros2_topic_echo(topic: str) -> dict:
    return _run_ros_cmd(["ros2", "topic", "echo", topic, "--once"], timeout=10.0)


def ros2_topic_pub(topic: str, msg_type: str, data: str) -> dict:
    return _run_ros_cmd(["ros2", "topic", "pub", topic, msg_type, data, "--once"])


def ros2_service_list() -> dict:
    return _run_ros_cmd(["ros2", "service", "list"])


def ros2_service_call(service_name: str, service_type: str, data: str) -> dict:
    return _run_ros_cmd(["ros2", "service", "call", service_name, service_type, data])


def ros2_node_list() -> dict:
    return _run_ros_cmd(["ros2", "node", "list"])


def ros2_param_get(node_name: str, param_name: str) -> dict:
    return _run_ros_cmd(["ros2", "param", "get", node_name, param_name])


def ros2_param_set(node_name: str, param_name: str, value: str) -> dict:
    return _run_ros_cmd(["ros2", "param", "set", node_name, param_name, value])
