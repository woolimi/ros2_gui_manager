"""Startup dependency checks."""

import platform
import subprocess
import sys


def check_and_install_dependencies():
    """Check required packages and optionally install them."""
    missing = []

    try:
        import PyQt5  # noqa: F401
    except ImportError:
        missing.append("PyQt5")

    if not missing:
        return True

    print("=" * 52)
    print("  ROS2 GUI Manager - 의존성 확인")
    print("=" * 52)
    print("\n  다음 패키지가 설치되어 있지 않습니다:")
    for package in missing:
        print(f"    - {package}")
    print()

    answer = input("  지금 설치하시겠습니까? [Y/n]: ").strip().lower()
    if answer not in ("", "y", "yes"):
        print("\n  설치를 취소했습니다.")
        print("  수동 설치 후 다시 실행해주세요:")
        print("    pip install PyQt5")
        print("    또는: bash install.sh")
        return False

    in_venv = sys.prefix != sys.base_prefix
    for package in missing:
        print(f"\n  [{package}] 설치 중...")
        if in_venv:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=False,
            )
        else:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package, "--break-system-packages"],
                capture_output=False,
            )
            if result.returncode != 0:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    capture_output=False,
                )

        if result.returncode == 0:
            print(f"  [OK] {package} 설치 완료")
            continue

        print(f"  [ERROR] {package} 설치 실패")
        print(f"  수동 설치: pip install {package}")
        if platform.system() == "Darwin":
            print("  또는:      brew install pyqt@5")
        else:
            print("  또는:      sudo apt install python3-pyqt5")
        return False

    print("\n  설치 완료. 프로그램을 시작합니다...\n")
    return True
