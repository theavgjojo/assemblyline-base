from inspect import getmembers, isfunction
from sys import exc_info
from traceback import format_tb


class ChainException(Exception):
    def __init__(self, message, cause=None):
        Exception.__init__(self, message)
        self.cause = cause


class NonRecoverableError(ChainException):
    pass


class RecoverableError(ChainException):
    pass


class ConfigException(Exception):
    pass


class Chain(object):
    """
    This class can be used as a decorator to override the type of exceptions returned by a function
    """

    def __init__(self, exception):
        self.exception = exception

    def __call__(self, original):
        def wrapper(*args, **kwargs):
            try:
                return original(*args, **kwargs)
            except Exception as e:
                wrapped = self.exception(str(e), e)
                raise wrapped.with_traceback(exc_info()[2])

        wrapper.__name__ = original.__name__
        wrapper.__doc__ = original.__doc__
        wrapper.__dict__.update(original.__dict__)

        return wrapper

    def execute(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            wrapped = self.exception(str(e), e)
            raise wrapped.with_traceback(exc_info()[2])


class ChainAll:
    """
    This class can be used as a decorator to override the type of exceptions returned by every method of a class
    """

    def __init__(self, exception):
        self.exception = Chain(exception)

    def __call__(self, cls):
        """We can use an instance of this class as a decorator."""
        for method in getmembers(cls, predicate=isfunction):
            setattr(cls, method[0], self.exception(method[1]))

        return cls


def get_stacktrace_info(ex: Exception) -> str:
    return ''.join(format_tb(exc_info()[2]) + [': '.join((ex.__class__.__name__, str(ex)))])
