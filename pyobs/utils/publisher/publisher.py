class Publisher:
    def open(self):
        """Open publisher."""
        pass

    def close(self):
        """Close publisher."""

    def __call__(self, **kwargs):
        """Publish the given results.

        Args:
            **kwargs: Results to publish.
        """
        raise NotImplementedError


__all__ = ['Publisher']
