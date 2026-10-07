from typing import Type

from app.channels.base import BaseChannel
from app.channels.reddit import RedditChannel
from app.channels.hackernews import HackerNewsChannel
from app.channels.linkedin import LinkedInChannel
from app.channels.twitter import TwitterChannel
from app.channels.threads import ThreadsChannel

__all__ = [
    "BaseChannel",
    "RedditChannel",
    "HackerNewsChannel",
    "LinkedInChannel",
    "TwitterChannel",
    "ThreadsChannel",
    "get_channel"
]

def get_channel(platform) -> Type[BaseChannel]:
    """Factory function to get the channel class by platform name."""
    channels = {
        'reddit': RedditChannel,
        'hackernews': HackerNewsChannel,
        'hn': HackerNewsChannel,
        'linkedin': LinkedInChannel,
        'twitter': TwitterChannel,
        'x': TwitterChannel,
        'threads': ThreadsChannel
    }
    key = platform.value.lower() if hasattr(platform, "value") else str(platform).lower()
    channel_cls = channels.get(key)
    if not channel_cls:
        raise ValueError(f"No channel implemented for platform: {platform}")

    return channel_cls

