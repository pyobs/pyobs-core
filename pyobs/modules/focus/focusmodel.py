import asyncio
import logging
from typing import Optional, Any, Dict, TYPE_CHECKING, cast
from py_expression_eval import Parser
import pandas as pd
import numpy as np
import numpy.typing as npt

if TYPE_CHECKING:
    import lmfit

from pyobs.interfaces import IFocuser, IFilters, IWeather, ITemperatures
from pyobs.modules import Module
from pyobs.modules import timeout
from pyobs.interfaces import IFocusModel
from pyobs.events import FocusFoundEvent, FilterChangedEvent, Event
from pyobs.utils.enums import WeatherSensors
from pyobs.utils.publisher import CsvPublisher
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class FocusModel(Module, IFocusModel):
    """A focus model that is automatically applied to an IFocuser.

    If, e.g., the model is defined as:

        model: -0.043807*T1 - 0.031798*T2 + 0.062042*temp + 41.694895

    Then "temp" is taken from the weather module automatically. The other temperatures must be defined, e.g., as:

        temperatures:
            T1:
                module: telescope
                sensor: T1
            T2:
                module: telescope
                sensor: T2

    In this case, the method get_temperatures() is called on the module "telescope" and the values T1 and T2 are
    taken for the model.

    Alternatively, the coefficients can be defined as symbols:

        model: a*T1 + b*T2 + c*temp + d

    For this to work, initial values must be specified separately:

        coefficients:
            a: -0.043807
            b: -0.031798
            c: 0.062042
            d: 41.694895

    Only this way it is possible to automatically re-calculate the model.
    """

    __module__ = "pyobs.modules.focus"

    def __init__(
        self,
        focuser: Optional[str] = None,
        weather: Optional[str] = None,
        interval: int = 300,
        temperatures: Optional[Dict[str, Dict[str, float]]] = None,
        model: Optional[str] = None,
        coefficients: Optional[Dict[str, float]] = None,
        update: bool = False,
        log_file: Optional[str] = None,
        min_measurements: int = 10,
        enabled: bool = True,
        temp_sensor: str = "average.temp",
        default_filter: Optional[str] = None,
        filter_offsets: Optional[Dict[str, float]] = None,
        filter_wheel: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize a focus model.

        Args:
            focuser: Name of focuser.
            weather: Name of weather station.
            interval: Interval for setting focus or None, if no regular setting of focus is required.
            model: Focus model to use.
            coefficients: Coefficients in model, mainly used when updating it.
            update: Whether to update the model on new focus values.
            log_file: Path to file containing all focus measurements.
            min_measurements: Minimum number of measurements to update model.
            enabled: If False, no focus is set.
            temp_sensor: Name of sensor at weather station to provide ambient temperature.
            default_filter: Name of default filter. If None, filters are ignored.
            filter_offsets: Offsets for different filters. If None, they are not modeled.
            filter_wheel: Name of filter wheel module to use for fetching filter before setting focus.
        """
        Module.__init__(self, **kwargs)

        # check import
        import lmfit

        log.info(f"Found lmfit {lmfit.__version__}.")

        # add thread func
        if interval is not None and interval > 0:
            self.add_background_task(self._update)

        # store
        self._focuser = focuser
        self._weather = weather
        self._interval = interval
        self._temperatures: Dict[str, Dict[str, float]] = {} if temperatures is None else temperatures
        self._focuser_ready = True
        self._coefficients = {} if coefficients is None else coefficients
        self._update_model = update
        self._min_measurements = min_measurements
        self._enabled = enabled
        self._temp_station, sensor = temp_sensor.split(".")
        self._temp_sensor = WeatherSensors(sensor)
        self._default_filter = default_filter
        self._filter_offsets = filter_offsets
        self._filter_wheel = filter_wheel
        log.info("Going to fetch temperature from sensor %s at station %s.", self._temp_sensor, self._temp_station)

        # model
        parser = Parser()
        log.info("Parsing model: %s", model)
        self._model = parser.parse(model)

        # coefficients
        if self._coefficients is not None and len(self._coefficients) > 0:
            log.info("Found coefficients: %s", ", ".join(["%s=%.3f" % (k, v) for k, v in self._coefficients.items()]))

        # variables
        variables = self._model.variables()
        for c in self._coefficients.keys():
            variables.remove(c)
        log.info("Found variables: %s", ", ".join(variables))

        # init log file
        self._publisher = None if log_file is None else CsvPublisher(log_file)

        # update model now?
        if update:
            self._calc_focus_model()

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # subscribe to events
        await self.comm.register_event(FocusFoundEvent, self._on_focus_found)
        if self._filter_offsets is not None and self._filter_wheel is not None:
            await self.comm.register_event(FilterChangedEvent, self._on_filter_changed)

    async def _update(self) -> None:
        # wait a little
        await asyncio.sleep(1)

        # run until closed
        while True:
            # if not enabled, just sleep a little
            if not self._enabled:
                await asyncio.sleep(1)
                continue

            # get focuser
            try:
                focuser = await self.proxy(self._focuser, IFocuser)
            except ValueError:
                log.warning("Could not connect to focuser.")
                await asyncio.sleep(10)
                continue

            # is focuser ready?
            status = await focuser.is_ready()
            if status is False:
                # log
                if self._focuser_ready:
                    log.info("Focuser not ready, waiting for it...")
                    self._focuser_ready = False

                # sleep a little and continue
                await asyncio.sleep(10)
                continue

            # came from not ready state?
            if not self._focuser_ready:
                log.info("Focuser ready now, starting focus tracking...")
                self._focuser_ready = True

            # now set focus
            try:
                # set optimal focus
                await self.set_optimal_focus()
            except ValueError:
                # something went wrong, wait a little and continue
                await asyncio.sleep(10)
                continue

            # sleep interval
            log.info("Going to sleep for %d seconds...", self._interval)
            await asyncio.sleep(self._interval)

    async def _get_optimal_focus(self, filter_name: Optional[str] = None, **kwargs: Any) -> float:
        """Returns the optimal focus.

        Args:
            filter_name: If given, use this filter name instead of fetching one.

        Returns:
            Optimum focus calculated from model.

        Raises:
            ValueError: If anything went wrong.
        """

        # get values for variables
        values = await self._get_values()

        # evaluate model
        log.info("Evaluating model...")
        focus = self._model.evaluate({**values, **self._coefficients})

        # focus offset?
        if self._filter_offsets is not None and self._filter_wheel is not None:
            try:
                # need a filter name?
                if filter_name is None:
                    # get proxy
                    wheel = await self.proxy(self._filter_wheel, IFilters)

                    # get filter
                    filter_name = await wheel.get_filter()

                # add offset
                offset = self._filter_offsets[filter_name]
                log.info("Adding filter offset of %.2f for filter %s...", offset, filter_name)
                focus += offset

            except (ValueError, KeyError):
                log.error("Could not determine filter offset.")

        # set focus
        log.info("Found optimal focus of %.4f.", focus)
        return float(focus)

    async def get_optimal_focus(self, **kwargs: Any) -> float:
        """Returns the optimal focus.

        Returns:
            Optimum focus calculated from model.

        Raises:
            ValueError: If anything went wrong.
        """
        return await self._get_optimal_focus()

    async def _get_values(self) -> Dict[str, Any]:
        """Retrieve all required values for the model.

        Returns:
            Dictionary containing all values required by the model.
        """

        # variables for model evaluation
        variables = {}

        # do we need a weather proxy?
        if "temp" in self._model.variables():
            log.info("Fetching temperature from weather module...")

            # get weather proxy
            try:
                weather = await self.proxy(self._weather, IWeather)
            except ValueError:
                raise ValueError("Could not connect to weather module.")

            # get value
            time, val = await weather.get_sensor_value(self._temp_station, self._temp_sensor)
            if val is None:
                raise ValueError("Received invalid temperature from weather station.")

            # get temperature
            variables["temp"] = val
            log.info("Got temperature of %.2f.", variables["temp"])

        # loop other temperatures
        module_temps = {}
        for var, cfg in self._temperatures.items():
            # need to fetch temperatures from module?
            if cfg["module"] not in module_temps:
                log.info("Fetching temperatures from module %s...", cfg["module"])

                # get proxy
                proxy = await self.proxy(cfg["module"], ITemperatures)

                # get temperatures
                module_temps[cfg["module"]] = await proxy.get_temperatures()

                # log
                vals = ", ".join(["%s=%.2f" % (k, v) for k, v in module_temps[cfg["module"]].items()])
                log.info("Received temperatures: %s", vals)

            # store, what we need
            if cfg["sensor"] not in module_temps[cfg["module"]]:
                raise ValueError(
                    "Temperature for sensor %s not in data from module %s." % (cfg["sensor"], cfg["module"])
                )
            variables[var] = module_temps[cfg["module"]][cfg["sensor"]]

        # log
        vals = ", ".join(["%s=%.2f" % (k, v) for k, v in variables.items()])
        log.info("Found values for model: %s", vals)
        return variables

    async def _set_optimal_focus(self, filter_name: Optional[str] = None, **kwargs: Any) -> None:
        """Sets optimal focus.

        Args:
            filter_name: Name of filter to use.

        Raises:
            ValueError: If anything went wrong.
        """

        # get focuser
        focuser = await self.proxy(self._focuser, IFocuser)

        # get focus
        focus = await self._get_optimal_focus(filter_name=filter_name)

        # set it
        log.info("Setting optimal focus...")
        await focuser.set_focus(focus)
        log.info("Done.")

    @timeout(60)
    async def set_optimal_focus(self, **kwargs: Any) -> None:
        """Sets optimal focus.

        Raises:
            ValueError: If anything went wrong.
        """
        await self._set_optimal_focus()

    async def _on_focus_found(self, event: Event, sender: str) -> bool:
        """Receive FocusFoundEvent.

        Args:
            event: The event itself
            sender: The name of the sender.
        """
        if not isinstance(event, FocusFoundEvent):
            raise ValueError("Not a focus event.")
        log.info("Received new focus of %.4f +- %.4f.", event.focus, event.error)

        # collect values for model
        values = await self._get_values()

        # add focus and datetime
        values["focus"] = event.focus
        values["error"] = event.error
        values["datetime"] = Time.now().isot
        values["filter"] = event.filter_name

        # write log
        if self._publisher is not None:
            await self._publisher(**values)

        # finally, calculate new model
        log.info("Re-calculating model...")
        await self._calc_focus_model()

        # finished
        log.info("Done.")
        return True

    async def _calc_focus_model(self) -> None:
        """Calculate new focus model from saved entries."""
        import lmfit

        # no coefficients? no model...
        if not self._coefficients or self._publisher is None:
            return

        # only take clear filter images for now
        data = await self._publisher.data()

        # enough measurements?
        if len(data) < self._min_measurements:
            log.warning(
                "Not enough measurements found for re-calculating model (%d<%d).", len(data), self._min_measurements
            )
            return

        # build parameters
        params = lmfit.Parameters()
        for c in self._coefficients.keys():
            params.add(c, 0.0)

        # if we want to fit filter offsets, add them to params
        if self._filter_offsets is not None:
            # get unique list of filters and add them
            for f in data["filter"].unique():
                params.add("off_" + f, 0.0)

        # fit
        log.info("Fitting coefficients...")
        out = lmfit.minimize(self._residuals, params, args=(data,))
        if not hasattr(out, "params"):
            raise ValueError("No params returned from fit.")
        out_params = getattr(out, "params")

        # print results
        log.info("Found best coefficients:")
        for p in out_params:
            if not p.startswith("off_"):
                if out_params[p].stderr is not None:
                    log.info("  %-5s = %10.5f +- %8.5f", p, out_params[p].value, out_params[p].stderr)
                else:
                    log.info("  %-5s = %10.5f", p, out_params[p].value)
        if self._filter_offsets is not None:
            log.info("Found filter offsets:")
            for p in out_params:
                if p.startswith("off_"):
                    if out_params[p].stderr is not None:
                        log.info("  %-10s = %10.5f +- %8.5f", p[4:], out_params[p].value, out_params[p].stderr)
                    else:
                        log.info("  %-10s = %10.5f", p[4:], out_params[p].value)

        rms = np.sqrt(np.mean(out.residual ** 2))
        log.info("Reduced chi squared: %.3f, RMS: %.3f", out.redchi, rms)

        # store new coefficients and filter offsets
        if self._update_model:
            # just copy all?
            d = dict(out_params.valuesdict())
            if self._filter_offsets is None:
                self._coefficients = d
            else:
                # need to separate
                self._coefficients = {k: v for k, v in d.items() if not k.startswith("off_")}
                self._filter_offsets = {k[4:]: v for k, v in d.items() if k.startswith("off_")}

    def _residuals(self, x: "lmfit.Parameters", data: pd.DataFrame) -> npt.NDArray[float]:
        """Fit method for model

        Args:
            x: Paramaters to evaluate.
            data: Full data set.

        Returns:

        """

        # calc model
        focus, model, error = [], [], []
        for _, row in data.iterrows():
            # how do we fit?
            if self._default_filter is None:
                # just fit it
                mod = self._model.evaluate({**x.valuesdict(), **row})

            else:
                # do we want to fit filter offsets?
                if self._filter_offsets:
                    # evaluate and add offset
                    mod = self._model.evaluate({**x.valuesdict(), **row})
                    if row["filter"] != self._default_filter:
                        mod += x["off_" + row["filter"]]

                else:
                    # no filter offsets, so ignore this row if, if wrong filter
                    if row["filter"] == self._default_filter:
                        mod = self._model.evaluate({**x.valuesdict(), **row})
                    else:
                        continue

            # add it
            model.append(mod)
            focus.append(row["focus"])
            error.append(row["error"])

        # return residuals
        return cast(npt.NDArray[float], (np.array(focus) - np.array(model)) / np.array(error))

    async def _on_filter_changed(self, event: Event, sender: str) -> bool:
        """Receive FilterChangedEvent and set focus.

        Args:
            event: The event itself
            sender: The name of the sender.
        """

        # wrong sender?
        if sender != self._filter_wheel or not isinstance(event, FilterChangedEvent):
            return False

        # log and change
        try:
            log.info("Detected filter change to %s, adjusting focus...", event.filter)
            await self._set_optimal_focus(event.filter)
            return True
        except ValueError:
            log.error("Could not set focus.")
            return False


__all__ = ["FocusModel"]
