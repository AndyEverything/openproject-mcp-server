from openproject_mcp.utils.logging import configure_logging
from openproject_mcp.config import Settings
from openproject_mcp.server import build_server

def run():
    configure_logging()
    _ = Settings()
    server = build_server()
    server.run()
