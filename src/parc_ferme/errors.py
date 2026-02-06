class ParcFermeError(Exception):
    """Base exception for parc-ferme."""


class ToolNotFoundError(ParcFermeError):
    """Raised when gh or claude CLI is not found."""


class PRNotFoundError(ParcFermeError):
    """Raised when the PR cannot be found."""


class GitHubError(ParcFermeError):
    """Raised when a GitHub operation (comment, API call) fails."""


class ConfigError(ParcFermeError):
    """Raised for config file parsing or validation errors."""


class ReviewError(ParcFermeError):
    """Raised when the Claude review process fails."""
