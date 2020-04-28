import os
import platform
from pathlib import Path
from click import get_app_dir

# HOME = os.getenv('HOME', os.getenv('USERPROFILE'))
# XDG_CONF_DIR = os.getenv('XDG_CONFIG_HOME', Path(HOME) / '.config')

# CONF_DIR = Path(XDG_CONF_DIR) / 'clinja'
CONF_DIR = Path(get_app_dir('clinja'))
DYNAMIC_FILE = CONF_DIR / 'dynamic.py'
STATIC_FILE = CONF_DIR / 'static.json'


DYNAMIC_FILE_INIT = """\
# This is the config file for clinja.
# The following variables are provided at run time:

# TEMPLATE (Path): Path to the template, is None when using stdin.
# DESTINATION (Path): Path to the destination, is None when using stdout.
# RUN_CWD (Path): Directory were the clinja command was run.
# STATIC_VARS (dict): Dictionary of static variable names and values.
# DYNAMIC_VARS (dict): Dictionary of dynamic variable names and values.

# This file should populate the DYNAMIC_VARS dictionary with any variable
# names and values it can determine from the provided variables.
"""

STATIC_FILE_INIT = """\
{
}
"""
