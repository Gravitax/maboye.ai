
"""
Agent Profiles

Defines specialized agent configurations with specific tools and prompts.
Each profile configures an agent for a particular domain expertise.
"""

import os
import json
from core.logger import logger

ALL_PROFILES = []

def _load_profiles_from_json():
    """Load agent profiles from JSON files."""
    profiles = []
    profiles_dir = os.path.dirname(__file__)

    if not os.path.exists(profiles_dir):
        return profiles

    for filename in os.listdir(profiles_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(profiles_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    profile = json.load(f)
                    profiles.append(profile)
            except Exception as e:
                pass
    return profiles

ALL_PROFILES = _load_profiles_from_json()

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
    'ALL_PROFILES',
    'get_profile_by_name',
    'get_all_profile_names'
]
