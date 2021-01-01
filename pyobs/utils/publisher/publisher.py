from pyobs.object import Object


class Publisher(Object):
    def __init__(self, *args, **kwargs):
        Object.__init__(self, *args, **kwargs)

    def __call__(self, **kwargs):
        """Publish the given results.

        Args:
            **kwargs: Results to publish.
        """
        raise NotImplementedError


__all__ = ['Publisher']
