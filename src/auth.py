"""Authentication middleware for HTTP transport."""

import os
from typing import Dict, Optional


class APIKeyAuth:
    """Simple API Key authentication for HTTP transport."""

    def __init__(self, valid_keys: Optional[Dict[str, str]] = None):
        """
        Initialize API Key authentication.

        Args:
            valid_keys: Dict mapping API keys to user names
                       e.g., {"user1-key": "User 1", "user2-key": "User 2"}
                       If None, loads from environment variable MCP_API_KEYS
        """
        if valid_keys is None:
            self.valid_keys = load_api_keys_from_env()
        else:
            self.valid_keys = valid_keys

    def validate(self, api_key: str) -> Optional[str]:
        """Validate API key and return user name if valid.

        Args:
            api_key: The API key to validate

        Returns:
            User name if valid, None otherwise
        """
        return self.valid_keys.get(api_key)


def load_api_keys_from_env() -> Dict[str, str]:
    """Load API keys from environment variable.

    Format: MCP_API_KEYS=key1:User1,key2:User2,key3:User3

    Returns:
        Dict mapping API keys to user names
    """
    keys_env = os.getenv("MCP_API_KEYS", "")
    valid_keys = {}

    if not keys_env:
        print("[WARNING] No MCP_API_KEYS environment variable set. HTTP auth disabled.")
        return valid_keys

    for pair in keys_env.split(","):
        if ":" in pair:
            key, name = pair.split(":", 1)
            valid_keys[key.strip()] = name.strip()

    print(f"[INFO] Loaded {len(valid_keys)} API keys from environment")
    return valid_keys


def extract_bearer_token(auth_header: str) -> Optional[str]:
    """Extract bearer token from Authorization header.

    Args:
        auth_header: Authorization header value

    Returns:
        Token if found, None otherwise
    """
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    return auth_header[7:]  # Remove "Bearer " prefix
