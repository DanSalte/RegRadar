class SystemicError(Exception):
    """Aborts the run (ADR-0007): bad credentials, source down, config."""


class AuthenticationError(SystemicError):
    pass


class SourceUnavailableError(SystemicError):
    pass


class ConfigurationError(SystemicError):
    pass


class InvalidDocumentError(Exception):
    """A single document could not be processed; the run continues."""
