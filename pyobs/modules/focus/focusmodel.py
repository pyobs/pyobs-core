import io
import logging

import typing
from py_expression_eval import Parser
import pandas as pd
import lmfit
import numpy as np

from pyobs import PyObsModule
from pyobs.modules import timeout
from pyobs.interfaces import IFocuser, IMotion, IWeather, ITemperatures, IFocusModel, IFilters
from pyobs.events import FocusFoundEvent
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class FocusModel(PyObsModule, IFocusModel):
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

    def __init__(self, focuser: str = None, weather: str = None, interval: int = 300, temperatures: dict = None,
                 model: str = None, coefficients: dict = None, update: bool = False,
                 measurements: str = '/pyobs/focus_model.csv', min_measurements: int = 10, enabled: bool = True,
                 temp_sensor: str = 'average.temp', default_filter: str = None, filter_offsets: dict = None,
                 filter_wheel: typing.Union[str, IFilters] = None, *args, **kwargs):
        """Initialize a focus model.

        Args:
            focuser: Name of focuser.
            weather: Name of weather station.
            interval: Interval for setting focus or None, if no regular setting of focus is required.
            model: Focus model to use.
            coefficients: Coefficients in model, mainly used when updating it.
            update: Whether to update the model on new focus values.
            measurements: Path to file containing all focus measurements.
            min_measurements: Minimum number of measurements to update model.
            enabled: If False, no focus is set.
            temp_sensor: Name of sensor at weather station to provide ambient temperature.
            default_filter: Name of default filter. If None, filters are ignored.
            filter_offsets: Offsets for different filters. If None, they are not modeled.
            filter_wheel: Name of filter wheel module to use for fetching filter before setting focus.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # add thread func
        if interval is not None and interval > 0:
            self._add_thread_func(self._run_thread, True)

        # store
        self._focuser = focuser
        self._weather = weather
        self._interval = interval
        self._temperatures = temperatures = {} if temperatures is None else temperatures
        self._focuser_ready = True
        self._coefficients = {} if coefficients is None else coefficients
        self._update_model = update
        self._min_measurements = min_measurements
        self._enabled = enabled
        self._temp_station, self._temp_sensor = temp_sensor.split('.')
        self._default_filter = default_filter
        self._filter_offsets = filter_offsets
        self._filter_wheel = filter_wheel
        log.info('Going to fetch temperature from sensor %s at station %s.', self._temp_sensor, self._temp_station)

        # model
        parser = Parser()
        log.info('Parsing model: %s', model)
        self._model = parser.parse(model)

        # coefficients
        if self._coefficients is not None and len(self._coefficients) > 0:
            log.info('Found coefficients: %s', ', '.join(['%s=%.3f' % (k, v) for k, v in self._coefficients.items()]))

        # variables
        variables = self._model.variables()
        for c in self._coefficients.keys():
            variables.remove(c)
        log.info('Found variables: %s', ', '.join(variables))

        # load measurements
        self._measurements_file = measurements
        self._measurements = None
        self._load_measurements()

        # update model now?
        if update:
            self._calc_focus_model()

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # subscribe to events
        self.comm.register_event(FocusFoundEvent, self._on_focus_found)

    def _run_thread(self):
        # wait a little
        self.closing.wait(1)

        # run until closed
        while not self.closing.is_set():
            # if not enabled, just sleep a little
            if not self._enabled:
                self.closing.wait(1)
                continue

            # get focuser
            try:
                focuser: IFocuser = self.proxy(self._focuser, IFocuser)
            except ValueError:
                log.warning('Could not connect to focuser.')
                self.closing.wait(60)
                continue

            # is focuser ready?
            status = focuser.is_ready().wait()
            if status is False:
                # log
                if self._focuser_ready:
                    log.info('Focuser not ready, waiting for it...')
                    self._focuser_ready = False

                # sleep a little and continue
                self.closing.wait(10)
                continue

            # came from not ready state?
            if not self._focuser_ready:
                log.info('Focuser ready now, starting focus tracking...')
                self._focuser_ready = True

            # now set focus
            try:
                # set optimal focus
                self.set_optimal_focus()
            except ValueError:
                # something went wrong, wait a little and continue
                self.closing.wait(60)
                continue

            # sleep interval
            log.info('Going to sleep for %d seconds...', self._interval)
            self.closing.wait(self._interval)

    def get_optimal_focus(self, *args, **kwargs) -> float:
        """Returns the optimal focus.

        Returns:
            Optimum focus calculated from model.

        Raises:
            ValueError: If anything went wrong.
        """

        # get values for variables
        values = self._get_values()

        # evaluate model
        log.info('Evaluating model...')
        focus = self._model.evaluate({**values, **self._coefficients})

        # focus offset?
        if self._filter_offsets is not None and self._filter_wheel is not None:
            # get proxy
            wheel: IFilters = self.proxy(self._filter_wheel, IFilters)

            # get filter
            filter_name = wheel.get_filter().wait()

            # add offset
            offset = self._filter_offsets[filter_name]
            log.info('Adding filter offset of %.2f...', offset)
            focus += offset

        # set focus
        log.info('Found optimal focus of %.4f.', focus)
        return float(focus)

    def _get_values(self) -> dict:
        """Retrieve all required values for the model.

        Returns:
            Dictionary containing all values required by the model.
        """

        # variables for model evaluation
        variables = {}

        # do we need a weather proxy?
        if 'temp' in self._model.variables():
            log.info('Fetching temperature from weather module...')

            # get weather proxy
            try:
                weather: IWeather = self.proxy(self._weather, IWeather)
            except ValueError:
                raise ValueError('Could not connect to weather module.')

            # get value
            time, val = weather.get_sensor_value(self._temp_station, self._temp_sensor).wait()
            if val is None:
                raise ValueError('Received invalid temperature from weather station.')

            # get temperature
            variables['temp'] = val
            log.info('Got temperature of %.2f.', variables['temp'])

        # loop other temperatures
        module_temps = {}
        for var, cfg in self._temperatures.items():
            # need to fetch temperatures from module?
            if cfg['module'] not in module_temps:
                log.info('Fetching temperatures from module %s...', cfg['module'])

                # get proxy
                proxy: ITemperatures = self.proxy(cfg['module'], ITemperatures)

                # get temperatures
                module_temps[cfg['module']] = proxy.get_temperatures().wait()

                # log
                vars = ', '.join(['%s=%.2f' % (k, v) for k, v in module_temps[cfg['module']].items()])
                log.info('Received temperatures: %s', vars)

            # store, what we need
            if cfg['sensor'] not in module_temps[cfg['module']]:
                raise ValueError('Temperature for sensor %s not in data from module %s.' %
                                 (cfg['sensor'], cfg['module']))
            variables[var] = module_temps[cfg['module']][cfg['sensor']]

        # log
        vars = ', '.join(['%s=%.2f' % (k, v) for k, v in variables.items()])
        log.info('Found values for model: %s', vars)
        return variables

    @timeout(60000)
    def set_optimal_focus(self, *args, **kwargs):
        """Sets optimal focus.

        Raises:
            ValueError: If anything went wrong.
        """

        # get focuser
        focuser: IFocuser = self.proxy(self._focuser, IFocuser)

        # get focus
        focus = self.get_optimal_focus()

        # set it
        log.info('Setting optimal focus...')
        focuser.set_focus(focus).wait()
        log.info('Done.')

    def _on_focus_found(self, event: FocusFoundEvent, sender: str):
        """Receive FocusFoundEvent.

        Args:
            event: The event itself
            sender: The name of the sender.
        """
        log.info('Received new focus of %.4f +- %.4f.', event.focus, event.error)

        # collect values for model
        values = self._get_values()

        # add focus and datetime
        values['focus'] = event.focus
        values['error'] = event.error
        values['datetime'] = Time.now().isot
        values['filter'] = event.filter_name

        # append or new?
        if self._measurements is None:
            # use values as new dataframe with one entry
            log.info('No previous measurements found, starting new file.')
            self._measurements = pd.DataFrame({k: [v] for k, v in values.items()})
        else:
            # append
            try:
                self._measurements = self._measurements.append(values, ignore_index=True)
            except TypeError:
                # wrong file format?
                log.error('Possibly wrong file format for %s, please fix or delete it.', self._measurements_file)
                return

        # write it back
        self._save_measurements()

        # finally, calculate new model
        log.info('Re-calculating model...')
        self._calc_focus_model()

        # finished
        log.info('Done.')

    def _load_measurements(self):
        try:
            # open file with previous measurements
            log.info('Reading previous measurements...')
            with self.open_file(self._measurements_file, 'r') as f:
                # read data and append values
                self._measurements = pd.read_csv(f, index_col=False)

        except (FileNotFoundError, pd.errors.EmptyDataError):
            # use values as new dataframe with one entry
            log.info('No previous measurements found, starting new file.')
            self._measurements = None

    def _save_measurements(self):
        # no measurements?
        if self._measurements is None:
            return

        # write to file
        with self.open_file(self._measurements_file, 'w') as f:
            log.info('Writing measurements to file...')
            with io.StringIO() as sio:
                self._measurements.to_csv(sio, index=False)
                f.write(sio.getvalue().encode('utf8'))

    def _calc_focus_model(self):
        """Calculate new focus model from saved entries."""

        # no coefficients? no model...
        if not self._coefficients or self._measurements is None:
            return

        # only take clear filter images for now
        data = self._measurements.copy()

        # enough measurements?
        if len(data) < self._min_measurements:
            log.warning('Not enough measurements found for re-calculating model (%d<%d).',
                        len(data), self._min_measurements)
            return

        # build parameters
        params = lmfit.Parameters()
        for c in self._coefficients.keys():
            params.add(c, 0.)

        # if we want to fit filter offsets, add them to params
        if self._filter_offsets is not None:
            # get unique list of filters and add them
            for f in data['filter'].unique():
                params.add('off_' + f, 0.)

        # fit
        log.info('Fitting coefficients...')
        out = lmfit.minimize(self._residuals, params, args=(data,))

        # print results
        log.info('Found best coefficients:')
        for p in out.params:
            if not p.startswith('off_'):
                if out.params[p].stderr is not None:
                    log.info('  %-5s = %10.5f +- %8.5f', p, out.params[p].value, out.params[p].stderr)
                else:
                    log.info('  %-5s = %10.5f', p, out.params[p].value)
        if self._filter_offsets is not None:
            log.info('Found filter offsets:')
            for p in out.params:
                if p.startswith('off_'):
                    if out.params[p].stderr is not None:
                        log.info('  %-10s = %10.5f +- %8.5f', p[4:], out.params[p].value, out.params[p].stderr)
                    else:
                        log.info('  %-10s = %10.5f', p[4:], out.params[p].value)

        log.info('Reduced chi squared: %.3f', out.redchi)

        # store new coefficients and filter offsets
        if self._update_model:
            # just copy all?
            d = dict(out.params.valuesdict())
            if self._filter_offsets is None:
                self._coefficients = d
            else:
                # need to separate
                self._coefficients = {k: v for k, v in d.items() if not k.startswith('off_')}
                self._filter_offsets = {k[4:]: v for k, v in d.items() if k.startswith('off_')}
                print(self._coefficients)
                print(self._filter_offsets)

    def _residuals(self, x: lmfit.Parameters, data: pd.DataFrame):
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
                    if row['filter'] != self._default_filter:
                        mod += x['off_' + row['filter']]

                else:
                    # no filter offsets, so ignore this row if, if wrong filter
                    if row['filter'] == self._default_filter:
                        mod = self._model.evaluate({**x.valuesdict(), **row})
                    else:
                        continue

            # add it
            model.append(mod)
            focus.append(row['focus'])
            error.append(row['error'])

        # to numpy arrays
        model = np.array(model)
        focus = np.array(focus)
        error = np.array(error)

        # return residuals
        return (focus - model) / error


__all__ = ['FocusModel']
