"""Shared application constants."""

import platform

IS_MAC = platform.system() == "Darwin"
MONO_FONT_FAMILY = "Menlo" if IS_MAC else "Monospace"
