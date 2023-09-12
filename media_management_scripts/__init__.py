from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("media_management_scripts")
except PackageNotFoundError:
    __version__ = "unknown version"
