# from https://gitlab.com/kipe/influx_logging_handler
import logging
import traceback
from typing import Any, Iterator, Tuple

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions

from pyobs.utils.time import Time


class InfluxHandler(logging.Handler):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        url: str,
        org: str,
        bucket: str,
        token: str,
        module: str,
        measurement: str = "logging",
        write_options: WriteOptions = SYNCHRONOUS,
    ) -> None:

        self.client = InfluxDBClient(url=url, token=token)
        self.write_api = self.client.write_api(write_options=write_options)
        self.org = org
        self.bucket = bucket
        self.measurement = measurement
        self.module = module
        super().__init__()

    @staticmethod
    def _get_additional_tags(record: logging.LogRecord) -> Iterator[Tuple[str, Any]]:
        if "tags" in record.__dict__ and isinstance(record.__dict__["tags"], dict):
            for key, value in record.__dict__["tags"].items():
                yield (key, value)

    def emit(self, record: logging.LogRecord) -> None:
        point = (
            Point(self.measurement)  # type: ignore
            .tag("timestamp", Time.now().isot)
            .tag("module", self.module)
            .tag("logger", record.name)
            .tag("level", record.levelname)
            .tag("level_number", record.levelno)
            .tag("filename", record.filename)
            .tag("line_number", record.lineno)
            .tag("function_name", record.funcName)
            .field("message", record.getMessage())
            .time(
                int(record.created * 1e6),
                write_precision=WritePrecision.US,
            )
        )

        for tag, value in self._get_additional_tags(record):
            point = point.tag(tag, value)

        exception = record.exc_info
        if exception:
            point = (
                point.tag("exception", "1")
                .tag("exception_type", exception[1].__class__.__name__)
                .field("traceback", "\n".join(traceback.format_tb(exception[2])).strip())
            )

        self.write_api.write(self.bucket, self.org, point)

    def flush(self) -> None:
        self.write_api.flush()  # type: ignore
        return super().flush()

    def close(self) -> None:
        self.write_api.close()  # type: ignore
        return super().close()
