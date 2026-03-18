#!/usr/bin/env python3
"""
ROS2 GUI Manager
A visual tool for managing ROS2 workspaces, packages, and nodes.
"""

import sys

from app.deps import check_and_install_dependencies


def main():
    from app.bootstrap import main as bootstrap_main

    bootstrap_main()


if __name__ == "__main__":
    if not check_and_install_dependencies():
        sys.exit(1)
    main()
#!/usr/bin/env python3
