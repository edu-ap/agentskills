"""
Auth Capabilities for Skills

Auth is NOT a skill. Auth is a capability requirement.
Like Unix file permissions - you either have access or you don't.

Philosophy (Linus/Carmack/Hotz consensus):
- Skills declare what auth they NEED, not how to get it
- Auth check runs BEFORE skill execution
- If auth is missing/expired, fail fast with clear error
- Token refresh happens transparently in the auth layer
- No middleware hell - direct capability checks

Auth Types (simplified from 8 patterns to 3):
1. env-token: Static token from .env (HubSpot, Slack, Fireflies, Linear, etc.)
2. oauth-google: Google OAuth with pickle cache (Gmail, GDrive, Calendar)
3. oauth-msal: Microsoft MSAL with device flow (Outlook, SharePoint, Teams)
"""

import os
import pickle
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from enum import Enum


class AuthMethod(Enum):
    """Supported authentication methods."""
    ENV_TOKEN = "env-token"      # Static token from .env file
    OAUTH_GOOGLE = "oauth-google"  # Google OAuth with pickle cache
    OAUTH_MSAL = "oauth-msal"     # Microsoft MSAL with device flow
    PUBLIC = "public"            # No auth required (Wayback, etc.)


@dataclass
class AuthCapability:
    """Definition of an auth capability."""

    name: str
    method: AuthMethod
    env_vars: list[str] = field(default_factory=list)  # Required env vars
    token_path: Optional[str] = None  # Path to cached token (for OAuth)
    scopes: list[str] = field(default_factory=list)  # OAuth scopes if applicable
    refresh_url: Optional[str] = None  # Token refresh endpoint
    description: str = ""

    def check(self) -> tuple[bool, str]:
        """
        Check if this capability is available.
        Returns (is_valid, message).
        """
        if self.method == AuthMethod.PUBLIC:
            return True, "Public API - no auth required"

        if self.method == AuthMethod.ENV_TOKEN:
            return self._check_env_token()

        if self.method == AuthMethod.OAUTH_GOOGLE:
            return self._check_google_token()

        if self.method == AuthMethod.OAUTH_MSAL:
            return self._check_msal_token()

        return False, f"Unknown auth method: {self.method}"

    def _check_env_token(self) -> tuple[bool, str]:
        """Check if required env vars are set."""
        missing = []
        for var in self.env_vars:
            if not os.getenv(var):
                missing.append(var)

        if missing:
            return False, f"Missing env vars: {', '.join(missing)}"

        return True, f"Token available ({self.env_vars[0]})"

    def _check_google_token(self) -> tuple[bool, str]:
        """Check if Google OAuth token exists and is valid."""
        if not self.token_path:
            return False, "No token path configured"

        token_file = Path(self.token_path).expanduser()
        if not token_file.exists():
            return False, f"Token not found: {token_file} (run OAuth flow)"

        try:
            with open(token_file, 'rb') as f:
                creds = pickle.load(f)

            if creds.valid:
                return True, "Token valid"

            if creds.expired and creds.refresh_token:
                return True, "Token expired but refreshable"

            return False, "Token expired and not refreshable (re-auth required)"
        except Exception as e:
            return False, f"Token read error: {e}"

    def _check_msal_token(self) -> tuple[bool, str]:
        """Check if MSAL token cache exists."""
        if not self.token_path:
            return False, "No token path configured"

        token_file = Path(self.token_path).expanduser()
        if not token_file.exists():
            return False, f"Token cache not found: {token_file} (run device flow)"

        try:
            with open(token_file, 'r') as f:
                cache = json.load(f)

            # Check if there are any access tokens
            if cache.get('AccessToken'):
                return True, "Token cache found"

            return False, "Token cache empty (re-auth required)"
        except Exception as e:
            return False, f"Token cache read error: {e}"


# ============================================================
# AUTH CAPABILITY REGISTRY
# ============================================================

AUTH_CAPABILITIES = {
    # === ENV TOKEN SERVICES ===
    "hubspot": AuthCapability(
        name="hubspot",
        method=AuthMethod.ENV_TOKEN,
        env_vars=["HUBSPOT_ACCESS_TOKEN"],
        description="HubSpot CRM API access",
    ),
    "slack": AuthCapability(
        name="slack",
        method=AuthMethod.ENV_TOKEN,
        env_vars=["SLACK_BOT_TOKEN"],
        description="Slack API (bot token for channels)",
    ),
    "slack-user": AuthCapability(
        name="slack-user",
        method=AuthMethod.ENV_TOKEN,
        env_vars=["SLACK_USER_TOKEN"],
        description="Slack API (user token for search)",
    ),
    "fireflies": AuthCapability(
        name="fireflies",
        method=AuthMethod.ENV_TOKEN,
        env_vars=["FIREFLIES_API_KEY"],
        description="Fireflies.ai meeting transcripts",
    ),
    "linear": AuthCapability(
        name="linear",
        method=AuthMethod.ENV_TOKEN,
        env_vars=["LINEAR_API_TOKEN"],
        description="Linear issue tracking",
    ),
    "perplexity": AuthCapability(
        name="perplexity",
        method=AuthMethod.ENV_TOKEN,
        env_vars=["PERPLEXITY_API_KEY"],
        description="Perplexity AI search",
    ),
    "github": AuthCapability(
        name="github",
        method=AuthMethod.ENV_TOKEN,
        env_vars=["GITHUB_TOKEN"],
        description="GitHub API access",
    ),
    "godaddy": AuthCapability(
        name="godaddy",
        method=AuthMethod.ENV_TOKEN,
        env_vars=["GODADDY_API_KEY", "GODADDY_API_SECRET"],
        description="GoDaddy DNS management",
    ),
    "elevenlabs": AuthCapability(
        name="elevenlabs",
        method=AuthMethod.ENV_TOKEN,
        env_vars=["ELEVENLABS_API_KEY"],
        description="ElevenLabs voice AI",
    ),
    "asana": AuthCapability(
        name="asana",
        method=AuthMethod.ENV_TOKEN,
        env_vars=["ASANA_TOKEN"],
        description="Asana task management",
    ),

    # === GOOGLE OAUTH SERVICES ===
    "gmail-personal": AuthCapability(
        name="gmail-personal",
        method=AuthMethod.OAUTH_GOOGLE,
        token_path="~/.cache/google_token_primary.pickle",
        scopes=["gmail.readonly", "gmail.compose"],
        description="Gmail personal account",
    ),
    "gmail-professional": AuthCapability(
        name="gmail-professional",
        method=AuthMethod.OAUTH_GOOGLE,
        token_path="~/.cache/google_token_professional.pickle",
        scopes=["gmail.readonly", "gmail.compose"],
        description="Gmail professional account",
    ),
    "gdrive": AuthCapability(
        name="gdrive",
        method=AuthMethod.OAUTH_GOOGLE,
        token_path="~/.cache/google_token_primary.pickle",
        scopes=["drive.readonly"],
        description="Google Drive access",
    ),
    "google-calendar": AuthCapability(
        name="google-calendar",
        method=AuthMethod.OAUTH_GOOGLE,
        token_path="~/.cache/google_token_primary.pickle",
        scopes=["calendar.readonly"],
        description="Google Calendar access",
    ),

    # === MICROSOFT MSAL SERVICES ===
    "outlook": AuthCapability(
        name="outlook",
        method=AuthMethod.OAUTH_MSAL,
        token_path="~/.cache/outlook_msal_token_cache.json",
        scopes=["Mail.Read", "Mail.ReadWrite"],
        description="Outlook email access",
    ),
    "outlook-calendar": AuthCapability(
        name="outlook-calendar",
        method=AuthMethod.OAUTH_MSAL,
        token_path="~/.cache/outlook_msal_token_cache.json",
        scopes=["Calendars.Read"],
        description="Outlook calendar access",
    ),
    "sharepoint": AuthCapability(
        name="sharepoint",
        method=AuthMethod.OAUTH_MSAL,
        token_path="~/.cache/outlook_msal_token_cache.json",
        scopes=["Sites.Read.All"],
        description="SharePoint document access",
    ),
    "teams": AuthCapability(
        name="teams",
        method=AuthMethod.OAUTH_MSAL,
        token_path="~/.cache/outlook_msal_token_cache.json",
        scopes=["ChannelMessage.Read.All"],
        description="Microsoft Teams messages",
    ),

    # === PUBLIC APIS ===
    "wayback": AuthCapability(
        name="wayback",
        method=AuthMethod.PUBLIC,
        description="Internet Archive Wayback Machine",
    ),
}


def get_capability(name: str) -> Optional[AuthCapability]:
    """Get auth capability by name."""
    return AUTH_CAPABILITIES.get(name)


def check_capabilities(required: list[str]) -> tuple[bool, dict[str, tuple[bool, str]]]:
    """
    Check multiple auth capabilities.
    Returns (all_valid, {capability_name: (is_valid, message)}).
    """
    results = {}
    all_valid = True

    for cap_name in required:
        cap = get_capability(cap_name)
        if not cap:
            results[cap_name] = (False, f"Unknown capability: {cap_name}")
            all_valid = False
            continue

        valid, msg = cap.check()
        results[cap_name] = (valid, msg)
        if not valid:
            all_valid = False

    return all_valid, results


def check_skill_auth(skill_name: str, skill_services: list[str]) -> tuple[bool, str]:
    """
    Check if a skill has all required auth capabilities.
    Maps service names to auth capabilities.
    """
    # Service to capability mapping
    SERVICE_TO_AUTH = {
        "hubspot": "hubspot",
        "slack": "slack",
        "gmail": "gmail-personal",
        "outlook": "outlook",
        "fireflies": "fireflies",
        "perplexity": "perplexity",
        "github": "github",
        "godaddy": "godaddy",
        "elevenlabs": "elevenlabs",
        "asana": "asana",
        "linear": "linear",
        "google-calendar": "google-calendar",
        "outlook-calendar": "outlook-calendar",
        "sharepoint": "sharepoint",
        "teams": "teams",
        "google-drive": "gdrive",
        "wayback": "wayback",
        "tavily": "perplexity",  # Falls back to perplexity-style
        "serper": "perplexity",  # Falls back to perplexity-style
        "otter": "fireflies",    # Similar API pattern
        "local": None,           # No auth needed
    }

    required_caps = []
    for service in skill_services:
        cap_name = SERVICE_TO_AUTH.get(service)
        if cap_name:
            required_caps.append(cap_name)

    if not required_caps:
        return True, f"{skill_name}: No auth required"

    all_valid, results = check_capabilities(required_caps)

    if all_valid:
        return True, f"{skill_name}: All auth available"

    # Build error message
    missing = [cap for cap, (valid, _) in results.items() if not valid]
    return False, f"{skill_name}: Missing auth for {', '.join(missing)}"


# ============================================================
# CLI / TESTING
# ============================================================

def print_auth_status():
    """Print status of all auth capabilities."""
    print("=" * 60)
    print("AUTH CAPABILITY STATUS")
    print("=" * 60)

    # Group by method
    by_method = {}
    for name, cap in AUTH_CAPABILITIES.items():
        method = cap.method.value
        if method not in by_method:
            by_method[method] = []
        by_method[method].append((name, cap))

    for method, caps in by_method.items():
        print(f"\n[{method}]")
        for name, cap in caps:
            valid, msg = cap.check()
            status = "✓" if valid else "✗"
            print(f"  {status} {name}: {msg}")

    print()


if __name__ == "__main__":
    # Auth is read from environment variables
    # Set them before running: export HUBSPOT_ACCESS_TOKEN=xxx
    print_auth_status()
