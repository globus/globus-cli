from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LoginContext:
    # A string representing the shell command a user should issue to resolve their
    #   login-related issue
    login_command: str = "globus login"

    # Error message to display if the asserted login fails.
    error_message: str | None = None
