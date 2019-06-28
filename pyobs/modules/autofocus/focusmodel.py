import io
import logging
from py_expression_eval import Parser
import pandas as pd

from pyobs import PyObsModule
from pyobs.modules import timeout
from pyobs.interfaces import IFocuser, IMotion, IWeather, ITemperatures, IFocusModel
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
                 measurements: str = '/pyobs/focus_model.csv', min_measurements: int = 10,
                 *args, **kwargs):
        """Initialize a focus model.

        Args:
            focuser: Name of focuser.
            weather: Name of weather station.
            interval: Interval for setting focus or None, if no regular setting of focus is required.
            model: Focus model to use.
            coefficients: Coefficients in model, mainly used when updating it.
            update: Whether to update the model on new focus values.
            measurements: Path to file containing all focus measurements.

        """
        PyObsModule.__init__(self, thread_funcs=self._run_thread if interval is not None and interval > 0 else None,
                             *args, **kwargs)

        # store
        self._focuser = focuser
        self._weather = weather
        self._interval = interval
        self._temperatures = temperatures = {} if temperatures is None else temperatures
        self._focuser_ready = True
        self._coefficients = {} if coefficients is None else coefficients
        self._update_model = update
        self._measurements_file = measurements
        self._min_measurements = min_measurements

        # list of allowed focuser states for focussing:
        self._allowed_states = [IMotion.Status.IDLE, IMotion.Status.POSITIONED,
                                IMotion.Status.SLEWING, IMotion.Status.TRACKING]

        # model
        parser = Parser()
        log.info('Parsing model: %s', model)
        self._model = parser.parse(model)

        # coefficients
        if self._coefficients is not None and len(self._coefficients) > 0:
            log.info('Found coefficients: %s', ', '.join(['%s=%.3f' % (k, v) for k, v in self._coefficients.items()]))

        # variables
        variables = self._model.variables()
        for c in coefficients.keys():
            variables.remove(c)
        log.info('Found variables: %s', ', '.join(variables))

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
            # get focuser
            try:
                focuser: IFocuser = self.proxy(self._focuser, IFocuser)
            except ValueError:
                log.warning('Could not connect to focuser.')

            # it must be in allowed state
            status = focuser.get_motion_status('IFocuser').wait()
            if status not in self._allowed_states:
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
        log.info('Found optimal focus of %.4f.', focus)
        return focus

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

            # get all weather data
            data = weather.get_weather_status().wait()
            if IWeather.Sensors.TEMPERATURE.value not in data:
                raise ValueError('No temperature in weather data.')

            # get temperature
            variables['temp'] = data[IWeather.Sensors.TEMPERATURE.value]
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
        log.info('Received new focus of %.4f.', event.focus)

        # no update wanted?
        if not self._update_model:
            return

        # collect values for model
        values = self._get_values()

        # add focus and datetime
        values['focus'] = event.focus
        values['datetime'] = Time.now().isot

        try:
            # open file with previous measurements
            with self.open_file(self._measurements_file, 'r') as f:
                # read data and append values
                data = pd.read_csv(f, index_col=False).append(values, ignore_index=True)

        except (FileNotFoundError, pd.errors.EmptyDataError):
            # use values as new dataframe with one entry
            data = pd.DataFrame({k: [v] for k, v in values.items()})

        except TypeError:
            # wrong file format?
            log.error('Possibly wrong file format for %s, please fix or delete it.', self._measurements_file)
            return

        # write file back
        with self.open_file(self._measurements_file, 'w') as f:
            with io.StringIO() as sio:
                data.to_csv(sio, index=False)
                f.write(sio.getvalue().encode('utf8'))

        # finally, calculate new model
        self._calc_focus_model()

    def _calc_focus_model(self):
        """Calculate new focus model from saved entries."""

        try:
            # open file with previous measurements and read data
            with self.open_file(self._measurements_file, 'r') as f:
                data = pd.read_csv(f, index_col=False)
        except FileNotFoundError:
            log.warning('Could not find file with previous measurements at %s.', self._measurements_file)
            return
        except pd.errors.EmptyDataError:
            data = pd.DataFrame({})

        # enough measurements?
        if len(data) < self._min_measurements:
            log.warning('Not enough measurements found for re-calculating model (%d<%d).',
                        len(data), self._min_measurements)
            return


__all__ = ['FocusModel']
