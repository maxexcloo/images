"""Include the managed Radiance image and video runtime in the repository check suite."""

from radiance_image.test_backend import BackendTests
from radiance_image.test_lifecycle import LifecycleTests
from radiance_image.test_nodes import ImageRequestTests
from radiance_image.test_video import VideoJobTests, VideoRequestTests

__all__ = [
    "BackendTests",
    "ImageRequestTests",
    "LifecycleTests",
    "VideoJobTests",
    "VideoRequestTests",
]
