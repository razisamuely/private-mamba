# Cluster configuration — default (anonymous) values.
# To use your real credentials, create cluster_config.local.py (gitignored)
# with the same variables overridden.

REMOTE_USER = "user"
REMOTE_HOST = "cluster.institution.edu"
MAIL_USER = "user@institution.edu"
REMOTE_HOME = "/home/user/workspace/private-mamba"

try:
    from cluster_config_local import *  # noqa: F401,F403
except ImportError:
    pass
