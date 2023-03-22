"""
    Custom exceptions, managed in one place.
"""
import logging

logger = logging.getLogger(__name__)


# ######################################
# page-object-focused exceptions
# ######################################
class PageLoadException(Exception):
    """
        Raise this exception when a page fails its load validations.
        Capture the errors and make them available.
    """
    def __init__(self, errors=None):
        Exception.__init__(self, errors)
        self.errors = errors


class PageUnloadException(Exception):
    """
        Raise this exception when a page fails its unload validation.
        Capture the errors and make them available.
    """
    def __init__(self, errors=None):
        Exception.__init__(self, errors)
        self.errors = errors
