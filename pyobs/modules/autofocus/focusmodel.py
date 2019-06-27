import logging
from py_expression_eval import Parser

from pyobs import PyObsModule
from pyobs.interfaces import IFocuser, IMotion, IWeather, ITemperatures

log = logging.getLogger(__name__)


class FocusModel(PyObsModule):
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
    """

    def __init__(self, focuser: str = None, weather: str = None, interval: int = 300, temperatures: dict = None,
                 model: str = None, *args, **kwargs):
        """Initialize a focus model.

        Args:
            focuser: Name of focuser.
            weather: Name of weather station.
            interval: Interval for setting focus.

        """
        PyObsModule.__init__(self, thread_funcs=self._run_thread, restart_threads=False, *args, **kwargs)

        # store
        self._focuser = focuser
        self._weather = weather
        self._interval = interval
        self._temperatures = temperatures
        self._focuser_ready = True

        # model
        parser = Parser()
        self._model = parser.parse(model)
        log.info('Found variables in model: %s', ', '.join(self._model.variables()))

    def _run_thread(self):
        # wait a little
        self.closing.wait(1)

        # list of allowed focuser states for focussing:
        allowed_states = [IMotion.Status.IDLE, IMotion.Status.POSITIONED,
                          IMotion.Status.SLEWING, IMotion.Status.TRACKING]

        # run until closed
        while not self.closing.is_set():
            # get focuser
            focuser: IFocuser = self.proxy(self._focuser, IFocuser)

            # it must be in allowed state
            status = focuser.get_motion_status('IFocuser').wait()
            if status not in allowed_states:
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

            # variables for model evaluation
            variables = {}

            # do we need a weather proxy?
            if 'temp' in self._model.variables():
                log.info('Fetching temperature from weather module...')

                # get weather proxy
                weather: IWeather = self.proxy(self._weather, IWeather)

                # get all weather data
                data = weather.get_weather_status().wait()

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
                variables[var] = module_temps[cfg['module']][cfg['sensor']]

            # log
            vars = ', '.join(['%s=%.2f' % (k, v) for k, v in variables.items()])
            log.info('Found values for model: %s', vars)

            # evaluate model
            log.info('Evaluating model...')
            focus = self._model.evaluate(variables)

            # set it
            log.info('Setting optimum focus of %.4f...', focus)
            focuser.set_focus(focus).wait()
            log.info('Done.')

            # sleep interval
            log.info('Going to sleep for %d seconds...', self._interval)
            self.closing.wait(self._interval)


__all__ = ['FocusModel']
