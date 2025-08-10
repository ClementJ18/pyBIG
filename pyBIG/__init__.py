from .memory_archive import InMemoryArchive
from .disk_archive import InDiskArchive

Archive = InMemoryArchive
LargeArchive = InDiskArchive

__version__ = "0.6.2"

__all__ = ["InMemoryArchive", "InDiskArchive", "Archive", "LargeArchive"]
