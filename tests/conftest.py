"""Shared test setup.

Importing the tool modules pulls in ``src.server``, which requires OpenProject
credentials to construct its client. The tests never hit the network, so we set
dummy credentials before anything imports the server.
"""

import os

os.environ.setdefault("OPENPROJECT_URL", "https://openproject.test")
os.environ.setdefault("OPENPROJECT_API_KEY", "dummy-key-for-tests")
