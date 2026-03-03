class FlyInError(Exception):
    """Base class for all Fly-In project exceptions."""
    pass


class MapSyntaxError(FlyInError):
    """Raised when the file format is wrong (e.g., missing ':')."""
    pass


class MapLogicError(FlyInError):
    """Raised when the map is impossible."""
    pass


class MapConnectionError(FlyInError):
    """Raised when a connection references a non-existent hub."""
    pass
