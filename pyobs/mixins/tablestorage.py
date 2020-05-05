import io
import pandas as pd
import numpy as np
import logging
from typing import Dict, Type, Union

from pyobs import PyObsModule


log = logging.getLogger(__name__)


class TableStorageMixin:
    def __init__(self, filename: str, columns: Dict[str, Type], reload_always: bool = False):
        """Initializes a new mixing for table storage.

        Args:
            filename: Name of CSV file.
            columns: Definition of columns as label->type dict.
            reload_always: If True, always reload table before appending.
        """

        # store
        self.__table_storage_filename = filename
        self.__table_storage_columns = columns
        self.__table_storage_reload_always = reload_always

        # load data or init with empty dataframe if file doesn't exist or None if no filename is given
        if filename is None:
            self.__table_storage_data = None
        else:
            self.__table_storage_data = self.__load_table_storage_data()

    @property
    def _table_storage(self):
        return self.__table_storage_data

    def __empty_table_storage(self):
        """Initializes an empty table storage."""

        # create a series for every columns
        series = {label: pd.Series(dtype=data_type) for label, data_type in self.__table_storage_columns.items()}

        # init dataframe
        return pd.DataFrame(series)

    def __load_table_storage_data(self) -> pd.DataFrame:
        """Load the table from file."""

        # I'm a PyobsModule as well!
        self: Union[TableStorageMixin, PyObsModule]

        # try to load data
        try:
            # open file with previous measurements
            log.info('Reading table storage from %s...', self.__table_storage_filename)
            with self.open_file(self.__table_storage_filename, 'r') as f:
                # read data and return it
                return pd.read_csv(f, index_col=False, dtype=self.__table_storage_columns)

        except (FileNotFoundError, pd.errors.EmptyDataError):
            # on error, return empty dataframe
            log.info('No file for table storage found, creating new one...')
            return self.__empty_table_storage()

    def __save_table_storage_data(self, table: pd.DataFrame):
        """Save the table to file."""

        # I'm a PyobsModule as well!
        self: Union[TableStorageMixin, PyObsModule]

        # first, store it in memory
        self.__table_storage_data = table

        # open file to write
        log.info('Writing table storage to file...')
        with self.open_file(self.__table_storage_filename, 'w') as f:
            # create a StringIO as temporary write target
            with io.StringIO() as sio:
                # write table to sio
                table.to_csv(sio, index=False)

                # and write all content to file
                f.write(sio.getvalue().encode('utf8'))

    def _append_to_table_storage(self, **kwargs):
        """Append a new row to the storage table.

        Args:
            kwargs: Dictionary with column->value pairs.
        """

        # no filename given?
        if self.__table_storage_filename is None:
            # do nothing
            return

        # reload table?
        if self.__table_storage_reload_always:
            self.__table_storage_data = self.__load_table_storage_data()

        # get data for append
        append = {}
        for col in self.__table_storage_columns.keys():
            # does it exist in kwargs?
            append[col] = kwargs[col] if col in kwargs else None

        # append to table
        log.info('Appending new row to table storage...')
        try:
            table = self.__table_storage_data.append(append, ignore_index=True)
        except TypeError:
            # wrong file format?
            log.error('Possibly wrong file format for %s, please fix or delete it.', self.__table_storage_filename)
            return

        # save it
        self.__save_table_storage_data(table)


if __name__ == '__main__':
    tsm = TableStorageMixin('test.csv', {'Time': str, 'Focus': np.float})

