import os
import platform
from pathlib import Path

HOME = os.getenv('HOME', os.getenv('USERPROFILE'))
XDG_CONF_DIR = os.getenv('XDG_CONFIG_HOME', Path(HOME) / '.config')

CONF_DIR = Path(XDG_CONF_DIR) / 'clinja'
CONF_FILE = CONF_DIR / 'config.py'
STORE_FILE = CONF_DIR / 'store.json'


CONF_FILE_INIT = """\
# This is the config file for clinja.
# The following variables are provided at run time:
#
# TEMPLATE (Path): Path to the template, is None when using stdin.
# DESTINATION (Path): Path to the destination, is None when using stdout.
# RUN_CWD (Path): Directory were the clinja command was run.
# VARS (dict): Dictionary of variable names and values, to populate the
#   templates with.
"""

STORE_FILE_INIT = """\
{
}
"""
