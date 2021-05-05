import pandas as pd
import logging

from .publisher import Publisher


log = logging.getLogger(__name__)


class CsvPublisher(Publisher):
    def __init__(self, filename: str, *args, **kwargs):
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

        # load data
        try:
            # load it
            csv = self.vfs.read_csv(self._filename, index_col=False)

        except FileNotFoundError:
            # file not found, so start new with row
            log.warning('No previous CSV file found, creating new one...')
            csv = pd.DataFrame()

        # create new row from kwargs and append it
        row = pd.DataFrame(kwargs, index=[0])
        csv = pd.concat([csv, row], ignore_index=True)

        # write it
        self.vfs.write_csv(csv, self._filename, index=False)


__all__ = ['CsvPublisher']
