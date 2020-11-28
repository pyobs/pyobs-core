import os

from .publisher import Publisher


class CsvPublisher(Publisher):
    def __init__(self, filename: str = 'log.csv', *args, **kwargs):
        """Initialize new CSV publisher.

        Args:
            filename: Name of file to log in.
        """
        Publisher.__init__(self, *args, **kwargs)

        # store
        self._filename = filename

    def __call__(self, **kwargs):
        """Publish the given results.

        Args:
            **kwargs: Results to publish.
        """

        # does file exist?
        if os.path.exists(self._filename):
            # load header of file
            with open(self._filename, 'r') as f:
                columns = [c.strip() for c in f.readline().split(',')]

        else:
            # new file, just write header and remember columns
            columns = kwargs.keys()
            with open(self._filename, 'w') as f:
                f.write(','.join(columns) + '\n')

        # get column values
        values = [kwargs[c] if c in kwargs else None for c in columns]

        # write it
        with open(self._filename, 'a') as f:
            f.write(','.join([str(v) for v in values]) + '\n')


__all__ = ['CsvPublisher']
