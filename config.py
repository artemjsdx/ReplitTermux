"""
config.py — Single source of truth for all configuration values.
S: One responsibility — configuration only.
"""
import os, uuid

PORT  = int(os.environ.get("RT_PORT", 7474))
TOKEN = os.environ.get("RT_TOKEN", "rt-" + str(uuid.uuid4())[:16])
MAX_HISTORY     = int(os.environ.get("RT_MAX_HISTORY", 200))
CMD_TIMEOUT     = int(os.environ.get("RT_CMD_TIMEOUT", 60))
TUNNEL_KEEPALIVE = int(os.environ.get("RT_TUNNEL_KEEPALIVE", 30))
