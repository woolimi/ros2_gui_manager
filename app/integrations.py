"""External editor and terminal integrations."""

import shutil
import subprocess
from pathlib import Path

from .constants import IS_MAC
from .ros_env import BASH, find_setup_bash


def detect_editors():
    editor_candidates = [
        ("VS Code", "code"),
        ("VS Code Insiders", "code-insiders"),
        ("Cursor", "cursor"),
        ("Windsurf", "windsurf"),
        ("Antigravity", "antigravity"),
        ("Zed", "zed"),
        ("Sublime Text", "subl"),
        ("Atom", "atom"),
        ("Gedit", "gedit"),
        ("Kate", "kate"),
        ("KWrite", "kwrite"),
        ("Mousepad", "mousepad"),
        ("Featherpad", "featherpad"),
        ("Leafpad", "leafpad"),
        ("Pluma", "pluma"),
        ("Xed", "xed"),
        ("Lite XL", "lite-xl"),
        ("Lapce", "lapce"),
        ("Helix", "hx"),
        ("Neovim (GUI)", "nvim-qt"),
        ("Emacs (GUI)", "emacs"),
        ("Nano (terminal)", "xterm -e nano"),
        ("Vim (terminal)", "xterm -e vim"),
        ("Neovim (terminal)", "xterm -e nvim"),
    ]

    if IS_MAC:
        editor_candidates = [
            (label, f"osascript -e 'tell app \"Terminal\" to do script \"{cmd.split()[-1]}\"'")
            if cmd.startswith("xterm -e")
            else (label, cmd)
            for label, cmd in editor_candidates
        ]

    found = []
    for label, cmd in editor_candidates:
        executable = cmd.split()[0]
        if IS_MAC and executable == "osascript":
            actual_executable = cmd.split('"')[-2].split()[0]
            if shutil.which(actual_executable):
                found.append((label, cmd))
        elif shutil.which(executable):
            found.append((label, cmd))
    return found


def launch_editor(chosen_cmd, file_path):
    subprocess.Popen(chosen_cmd.split() + [file_path], start_new_session=True)


def open_terminal(cwd, distro="", workspace_path=None, domain_id="0"):
    cwd = Path(cwd)
    workspace_source = ""
    if workspace_path:
        setup = Path(workspace_path) / "install" / "setup.bash"
        if setup.exists():
            workspace_source = f"source {setup} && "

    env_inject = f"export ROS_DOMAIN_ID={domain_id} && "
    ros_setup = find_setup_bash(distro) if distro else None
    ros_source = f"source {ros_setup} && " if ros_setup else ""
    init = f"{env_inject}{ros_source}{workspace_source}{BASH}"

    if IS_MAC:
        if Path("/Applications/iTerm.app").exists():
            script = (
                'tell application "iTerm2"\n'
                "  create window with default profile\n"
                "  tell current session of current window\n"
                f'    write text "cd {cwd} && {init}"\n'
                "  end tell\n"
                "end tell"
            )
        else:
            script = (
                'tell application "Terminal" to activate\n'
                f'tell application "Terminal" to do script "cd {cwd} && {init}"'
            )
        subprocess.Popen(["osascript", "-e", script])
        return True

    for term in ["gnome-terminal", "xterm", "konsole", "x-terminal-emulator"]:
        if not shutil.which(term):
            continue
        if term == "gnome-terminal":
            subprocess.Popen([term, f"--working-directory={cwd}", "--", BASH, "-c", init])
        else:
            subprocess.Popen([term, "-e", f"{BASH} -c '{init}'"])
        return True
    return False


def launch_terminal_command(cmd):
    if IS_MAC:
        script = (
            'tell application "Terminal" to activate\n'
            f'tell application "Terminal" to do script "{cmd}; read -p \'[Press Enter to close]\'"'
        )
        subprocess.Popen(["osascript", "-e", script])
        return True

    for term in ["gnome-terminal", "xterm", "konsole"]:
        if not shutil.which(term):
            continue
        full = f"{BASH} -c '{cmd}; echo; read -p \"[Press Enter to close]\""
        if term == "gnome-terminal":
            subprocess.Popen([term, "--", BASH, "-c", f"{BASH} -c \"{cmd}\"; read -p '[Press Enter]'"])
        else:
            subprocess.Popen([term, "-e", full])
        return True
    return False


def launch_ros_tool(command_name, ros_setup, env):
    source_prefix = f"source {ros_setup} && " if ros_setup else ""
    subprocess.Popen([BASH, "-c", f"{source_prefix}{command_name}"], env=env)
