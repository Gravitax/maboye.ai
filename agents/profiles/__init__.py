"""
Agent Profiles

Defines specialized agent configurations with specific tools and prompts.
Each profile configures an agent for a particular domain expertise.
"""

from agents.profiles.code_agent import CODE_AGENT_PROFILE
from agents.profiles.git_agent import GIT_AGENT_PROFILE
from agents.profiles.bash_agent import BASH_AGENT_PROFILE


# All available profiles
ALL_PROFILES = [
    CODE_AGENT_PROFILE,
    GIT_AGENT_PROFILE,
    BASH_AGENT_PROFILE
]


def get_profile_by_name(name: str):
    """
    Get agent profile by name

    Args:
        name: Profile name (e.g., 'CodeAgent', 'GitAgent')

    Returns:
        Profile dictionary or None if not found
    """
    for profile in ALL_PROFILES:
        if profile["name"] == name:
            return profile
    return None


def get_all_profile_names():
    """
    Get list of all profile names

    Returns:
        List of profile names
    """
    return [profile["name"] for profile in ALL_PROFILES]


__all__ = [
    'CODE_AGENT_PROFILE',
    'GIT_AGENT_PROFILE',
    'BASH_AGENT_PROFILE',
    'ALL_PROFILES',
    'get_profile_by_name',
    'get_all_profile_names'
]
