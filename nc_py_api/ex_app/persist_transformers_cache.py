"""Import this file to automatically point TRANSFORMERS_CACHE to your application's persistent storage."""

import os

from .misc import persistent_storage

os.environ["TRANSFORMERS_CACHE"] = persistent_storage()
