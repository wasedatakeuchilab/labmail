"""
This module is aimed to customize behaviors depending on
the running environment (e.g. in a container) by enviroment variables.

If a better solution is found in the future, this module will be replaced with it.
"""

import os

GOOGLE_OAUTH_FLOW_HOST = os.environ.get("LABMAIL_GOOGLE_OAUTH_FLOW_HOST", "localhost")
GOOGLE_OAUTH_FLOW_PORT = os.environ.get("LABMAIL_GOOGLE_OAUTH_FLOW_PORT", 8080)
GOOGLE_OAUTH_FLOW_BIND = os.environ.get("LABMAIL_GOOGLE_OAUTH_FLOW_BIND", None)
