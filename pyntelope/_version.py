from importlib.metadata import version

try:
    __version__ = version("pyntelope")
except:  # NOQA: E722
    pass
