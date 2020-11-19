import os
import platform
from pathlib import Path

from click import get_app_dir

CONF_DIR = Path(get_app_dir("clinja"))
DYNAMIC_FILE = CONF_DIR / "dynamic.py"
STATIC_FILE = CONF_DIR / "static.json"


DYNAMIC_FILE_INIT = """\
# This is clinja's dynamic source.
# Use this file to dynamically compute jinja variables from the variables
# provided at run time:

# TEMPLATE (Path): Path to the template, is None when using stdin.
# DESTINATION (Path): Path to the destination, is None when using stdout.
# RUN_CWD (Path): Directory were the clinja command was run.
# STATIC_VARS (dict): Dictionary of static variables.

# This file should populate the DYNAMIC_VARS dictionary:

# DYNAMIC_VARS (dict): Dictionary of dynamic variables.
"""

STATIC_FILE_INIT = """\
{
}
"""
