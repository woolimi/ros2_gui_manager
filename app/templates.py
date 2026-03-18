"""Code templates for generated ROS2 nodes."""


class NodeTemplates:
    @staticmethod
    def python_node(package_name, node_name):
        class_name = "".join(word.capitalize() for word in node_name.split("_"))
        return f"""#!/usr/bin/env python3
\"\"\"
Node: {node_name}
Package: {package_name}
\"\"\"
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class {class_name}(Node):

    def __init__(self):
        super().__init__('{node_name}')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        self.timer = self.create_timer(0.5, self.timer_callback)
        self.i = 0
        self.get_logger().info(f'{class_name} node started.')

    def timer_callback(self):
        msg = String()
        msg.data = f'Hello from {node_name}: {{self.i}}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{{msg.data}}"')
        self.i += 1


def main(args=None):
    rclpy.init(args=args)
    node = {class_name}()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
"""

    @staticmethod
    def init_py():
        return "# ROS2 Python package\n"

    @staticmethod
    def update_setup_py(setup_py_path, package_name, node_name):
        if not setup_py_path.exists():
            return False

        content = setup_py_path.read_text()
        entry = f"            '{node_name} = {package_name}.{node_name}:main',"
        if f"'{node_name} =" in content:
            return True

        target = "'console_scripts': ["
        if target not in content:
            return False

        content = content.replace(target, f"{target}\n{entry}")
        setup_py_path.write_text(content)
        return True
