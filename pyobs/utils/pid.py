class PID:
    """
    Discrete PID control
    """

    def __init__(self, p=2.0, i=0.0, d=1.0, derivator=0, integrator=0, integrator_max=500, integrator_min=-500):
        # public variables
        self.Kp = p
        self.Ki = i
        self.Kd = d
        self.Derivator = derivator
        self.Integrator = integrator
        self.Integrator_max = integrator_max
        self.Integrator_min = integrator_min

        # read-only
        self._set_point = 0.0
        self._P_value = None
        self._D_value = None
        self._I_value = None
        self._error = 0.0

    def update(self, current_value):
        """Calculate PID output value for given reference input and feedback

        Args:
            current_value: last measured value.
        """

        self._error = current_value - self._set_point
        self._P_value = self.Kp * self.error
        self._D_value = self.Kd * (self.error - self.Derivator)
        self.Derivator = self.error
        self.Integrator += self.error
        if self.Integrator > self.Integrator_max:
            self.Integrator = self.Integrator_max
        elif self.Integrator < self.Integrator_min:
            self.Integrator = self.Integrator_min
        self._I_value = self.Integrator * self.Ki
        return self._P_value + self._I_value + self._D_value

    @property
    def setpoint(self):
        return self._set_point

    @setpoint.setter
    def setpoint(self, v):
        self._set_point = v
        self.Integrator = 0
        self.Derivator = 0

    @property
    def error(self):
        return self._error


__all__ = ['PID']
