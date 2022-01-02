class PID:
    """
    Discrete PID control
    """

    def __init__(
        self,
        p: float = 2.0,
        i: float = 0.0,
        d: float = 1.0,
        derivator: float = 0,
        integrator: float = 0,
        integrator_max: float = 500.0,
        integrator_min: float = -500.0,
    ):
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
        self._error = 0.0

    def update(self, current_value: float) -> float:
        """Calculate PID output value for given reference input and feedback

        Args:
            current_value: last measured value.
        """

        self._error = current_value - self._set_point
        P_value = self.Kp * self.error
        D_value = self.Kd * (self.error - self.Derivator)
        self.Derivator = self.error
        self.Integrator += self.error
        if self.Integrator > self.Integrator_max:
            self.Integrator = self.Integrator_max
        elif self.Integrator < self.Integrator_min:
            self.Integrator = self.Integrator_min
        I_value = self.Integrator * self.Ki
        return P_value + I_value + D_value

    @property
    def setpoint(self) -> float:
        return self._set_point

    @setpoint.setter
    def setpoint(self, v: float) -> None:
        self._set_point = v
        self.Integrator = 0
        self.Derivator = 0

    @property
    def error(self) -> float:
        return self._error


__all__ = ["PID"]
