from .IStoppable import IStoppable


class IAutoGuiding(IStoppable):
    def start(self, *args, **kwargs) -> bool:
        """Starts a service.

        Returns:
            (bool) Success.
        """
        raise NotImplementedError

    def stop(self, *args, **kwargs) -> bool:
        """Stops a service.

        Returns:
            (bool) Success.
        """
        raise NotImplementedError

    def is_running(self, *args, **kwargs) -> bool:
        """Whether a service is running.

        Returns:
            (bool) Service is running.
        """
        raise NotImplementedError


__all__ = ['IAutoGuiding']
