"""PiCli version information"""

__metaclass__ = type

try:
    import pkg_resources

    __version__ = pkg_resources.get_distribution("picli").version
except Exception:
    __version__ = "unknown"
