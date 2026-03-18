"""Persistent configuration and domain ID helpers."""

import json
from pathlib import Path


def cfg_path():
    config_dir = Path.home() / ".config" / "ros2_gui_manager"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def load_config():
    path = cfg_path()
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {"workspaces": []}


def save_config(config):
    cfg_path().write_text(json.dumps(config, indent=2))


def domain_id_path():
    return Path.home() / ".ros_domain_id"


def write_domain_id(value):
    domain_id_path().write_text(str(value))


def ensure_bashrc_prompt(domain_value):
    """Ensure ~/.bashrc contains a prompt command that mirrors domain id."""
    marker = "# ros2_gui_manager: domain id sync"
    bashrc = Path.home() / ".bashrc"
    prompt_cmd = (
        f"\n{marker}\n"
        "PROMPT_COMMAND='export ROS_DOMAIN_ID=$(cat ~/.ros_domain_id 2>/dev/null || echo 0)'\n"
    )

    if not domain_id_path().exists():
        write_domain_id(domain_value)

    if bashrc.exists() and marker not in bashrc.read_text():
        with bashrc.open("a") as handle:
            handle.write(prompt_cmd)
