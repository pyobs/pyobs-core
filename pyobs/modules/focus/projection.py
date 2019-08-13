import logging
from typing import Union
import threading
import numpy as np
from astropy.io import fits
from lmfit.models import GaussianModel
from scipy import optimize, ndimage

from pyobs.comm import RemoteException
from pyobs.interfaces import IFocuser, ICamera, IAutoFocus
from pyobs.events import FocusFoundEvent
from pyobs import PyObsModule
from pyobs.modules import timeout


log = logging.getLogger(__name__)


class AutoFocusProjection(PyObsModule, IAutoFocus):
    """Module for auto-focusing a telescope."""

    def __init__(self, focuser: Union[str, IFocuser], camera: Union[str, ICamera], offset: bool = False,
                 *args, **kwargs):
        """Initialize a new auto focus system.

        Args:
            focuser: Name of IFocuser.
            camera: Name of ICamera.
            offset: If True, offsets are used instead of absolute focus values.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store focuser and camera
        self._focuser = focuser
        self._camera = camera
        self._offset = offset
        self._abort = threading.Event()

        # storage for data
        self._data = []

    def open(self):
        """Open module"""
        PyObsModule.open(self)

        # register event
        self.comm.register_event(FocusFoundEvent)

        # check focuser and camera
        try:
            self.proxy(self._focuser, IFocuser)
            self.proxy(self._camera, ICamera)
        except ValueError:
            log.warning('Either camera or focuser do not exist or are not of correct type at the moment.')

    def close(self):
        """Close module."""

    @timeout(600000)
    def auto_focus(self, count: int, step: float, exposure_time: int, *args, **kwargs) -> (float, float):
        """Perform an auto-focus series.

        This method performs an auto-focus series with "count" images on each side of the initial guess and the given
        step size. With count=3, step=1 and guess=10, this takes images at the following focus values:
            7, 8, 9, 10, 11, 12, 13

        Args:
            count: Number of images to take on each side of the initial guess. Should be an odd number.
            step: Step size.
            exposure_time: Exposure time for images.

        Returns:
            Tuple of obtained best focus value and its uncertainty.

        Raises:
            ValueError: If focus could not be obtained.
            FileNotFoundException: If image could not be downloaded.
        """
        log.info('Performing auto-focus...')

        # get focuser
        log.info('Getting proxy for focuser...')
        focuser: IFocuser = self.proxy(self._focuser, IFocuser)

        # get camera
        log.info('Getting proxy for camera...')
        camera: ICamera = self.proxy(self._camera, ICamera)

        # get focus as first guess
        try:
            if self._offset:
                log.info('Using focus offset of 0mm as initial guess.')
            else:
                guess = focuser.get_focus().wait()
                log.info('Using current focus of %.2fmm as initial guess.', guess)
        except RemoteException:
            raise ValueError('Could not fetch current focus value.')

        # define array of focus values to iterate
        focus_values = np.linspace(guess - count * step, guess + count * step, 2 * count + 1)

        # define set_focus method
        set_focus = focuser.set_focus_offset if self._offset else focuser.set_focus

        # reset
        self._data = []
        self._abort = threading.Event()

        # loop focus values
        log.info('Starting focus series...')
        for foc in focus_values:
            # set focus
            log.info('Changing focus to %.2fmm...', foc)
            if self._abort.is_set():
                raise InterruptedError()
            try:
                set_focus(float(foc)).wait()
            except RemoteException:
                raise ValueError('Could not set new focus value.')

            # do exposure
            log.info('Taking picture...')
            if self._abort.is_set():
                raise InterruptedError()
            try:
                filename = camera.expose(exposure_time=exposure_time, image_type=ICamera.ImageType.FOCUS,
                                         count=1).wait()[0]
            except RemoteException:
                log.error('Could not take image.')

            # download image
            log.info('Downloading image...')
            try:
                with self.open_file(filename, 'rb') as f:
                    tmp = fits.open(f, memmap=False)
                    img = fits.PrimaryHDU(data=tmp[0].data, header=tmp[0].header)
                    tmp.close()
            except FileNotFoundError:
                raise ValueError('Could not download image.')

            # analyse
            log.info('Analysing picture...')
            try:
                self._analyse_image(foc, img.data)
            except:
                # do nothing..
                log.error('Could not analyse image.')

        # fit focus
        if self._abort.is_set():
            raise InterruptedError()
        focus = self._fit_focus()

        # check
        if focus is None or focus[0] is None or np.isnan(focus[0]):
            raise ValueError('Could not fit focus.')

        # "absolute" will be the absolute focus value, i.e. focus+offset
        absolute = None

        # log and set focus
        if self._offset:
            log.info('Setting new focus offset of (%.3f+-%.3f) mm.', focus[0], focus[1])
            absolute = focus[0] + focuser.get_focus().wait()
            focuser.set_focus_offset(focus[0]).wait()
        else:
            log.info('Setting new focus value of (%.3f+-%.3f) mm.', focus[0], focus[1])
            absolute = focus[0] + focuser.get_focus_offset().wait()
            focuser.set_focus(focus[0]).wait()

        # send event
        self.comm.send_event(FocusFoundEvent(absolute, focus[1]))

        # return result
        return focus[0], focus[1]

    def auto_focus_status(self, *args, **kwargs) -> dict:
        """Returns current status of auto focus.

        Returned dictionary contains a list of focus/fwhm pairs in X and Y direction.

        Returns:
            Dictionary with current status.
        """
        return self._data

    @timeout(20000)
    def abort(self, *args, **kwargs):
        """Abort current actions."""
        self._abort.set()

    def _analyse_image(self, focus, data, backsub=True, xbad=None, ybad=None):
        # clean data
        data = self._clean(data, backsub=backsub, xbad=xbad, ybad=ybad)

        # get projections
        xproj = np.mean(data, axis=0)  # PROJECTIONS
        yproj = np.mean(data, axis=1)
        nx = len(xproj)
        ny = len(yproj)

        # remove background gradient
        xclean = xproj - ndimage.uniform_filter1d(xproj, nx // 10)
        yclean = yproj - ndimage.uniform_filter1d(yproj, ny // 10)

        # get window functions
        xwind = self._window_function(xclean, border=3)
        ywind = self._window_function(yclean, border=3)

        # calculate correlation functions
        xavg = np.average(xclean)
        yavg = np.average(yclean)
        x = xwind * (xclean - xavg) / xavg
        y = ywind * (yclean - yavg) / yavg
        xcorr = np.correlate(x, x, mode='same')
        ycorr = np.correlate(y, y, mode='same')

        # filter out the peak (e.g. cosmics, ...)
        # imx = np.argmax(xcorr)
        # xcorr[imx] = 0.5 * (xcorr[imx - 1] + xcorr[imx + 1])
        # imx = np.argmax(ycorr)
        # ycorr[imx] = 0.5 * (ycorr[imx - 1] + ycorr[imx + 1])

        # fit cc functions to get fwhm
        xfit = self._fit_correlation(xcorr)
        yfit = self._fit_correlation(ycorr)

        # log it
        log.info('Found x=%.1f+-%.1f and y=%.1f+-%.1f.',
                     xfit.params['fwhm'].value, xfit.params['fwhm'].stderr,
                     yfit.params['fwhm'].value, yfit.params['fwhm'].stderr)

        # add to list
        self._data.append({'focus': focus,
                           'x': xfit.params['fwhm'].value, 'xerr': xfit.params['fwhm'].stderr,
                           'y': yfit.params['fwhm'].value, 'yerr': yfit.params['fwhm'].stderr})

    def _fit_focus(self) -> (float, float):
        # get data
        focus = [d['focus'] for d in self._data]
        xfwhm = [d['x'] for d in self._data]
        xsig = [d['xerr'] for d in self._data]
        yfwhm = [d['y'] for d in self._data]
        ysig = [d['yerr'] for d in self._data]

        # fit focus
        try:
            xfoc, xerr = self._fit_focus_curve(focus, xfwhm, xsig)
            yfoc, yerr = self._fit_focus_curve(focus, yfwhm, ysig)

            # weighted mean
            xerr = np.sqrt(xerr)
            yerr = np.sqrt(yerr)
            foc = (xfoc / xerr + yfoc / yerr) / (1. / xerr + 1. / yerr)
            err = 2. / (1. / xerr + 1. / yerr)
        except (RuntimeError, RuntimeWarning):
            raise ValueError('Could not find best focus.')

        # get min and max foci
        min_focus = np.min(focus)
        max_focus = np.max(focus)
        if foc < min_focus or foc > max_focus:
            raise ValueError("New focus out of bounds: {0:.3f}+-{1:.3f}mm.".format(foc, err))

        # return it
        return float(foc), float(err)

    @staticmethod
    def _window_function(arr, border=0):
        """
        Creates a sine window function of the same size as some 1-D array "arr".
        Optionally, a zero border at the edges is added by "scrunching" the window.
        """
        ndata = len(arr)
        nwind = ndata - 2 * border
        w = np.zeros(ndata)
        for i in range(nwind):
            w[i + border] = np.sin(np.pi * (i + 1.) / (nwind + 1.))
        return w

    @staticmethod
    def _clean(data, backsub=True, xbad=None, ybad=None):
        """
        Removes global slopes and fills up bad rows (ybad) or columns (xbad).
        """
        (ny, nx) = data.shape

        # REMOVE BAD COLUMNS AND ROWS
        if xbad is not None:
            x1 = xbad - 1
            if x1 < 0:
                x1 = 1
            x2 = x1 + 2
            if x2 >= nx:
                x2 = nx - 1
                x1 = x2 - 2
            for j in range(ny):
                data[j][xbad] = 0.5 * (data[j][x1] + data[j][x2])
        if ybad is not None:
            y1 = ybad - 1
            if y1 < 0:
                y1 = 1
            y2 = y1 + 2
            if y2 >= ny:
                y2 = ny - 1
                y1 = y2 - 2
            for i in range(nx):
                data[ybad][i] = 0.5 * (data[y1][i] + data[y2][i])

        # REMOVE GLOBAL SLOPES
        if backsub:
            xsl = np.median(data, axis=0)
            ysl = np.median(data, axis=1).reshape((ny, 1))
            xsl -= np.mean(xsl)
            ysl -= np.mean(ysl)
            xslope = np.tile(xsl, (ny, 1))
            yslope = np.tile(ysl, (1, nx))
            return data - xslope - yslope
        else:
            return data

    @staticmethod
    def _fit_correlation(correl):
        # create Gaussian model
        model = GaussianModel()

        # initial guess
        x = np.arange(len(correl))
        pars = model.guess(correl, x=x)
        pars['sigma'].value = 20.

        # fit
        return model.fit(correl, pars, x=x)

    @staticmethod
    def _fit_focus_curve(x_arr, y_arr, y_err):
        # initial guess
        ic = np.argmin(y_arr)
        ix = np.argmax(y_arr)
        b = y_arr[ic]
        c = x_arr[ic]
        x = x_arr[ix]
        slope = np.abs((y_arr[ic] - y_arr[ix]) / (c - x))
        a = b / slope

        # init
        p0 = [a, b, c]

        # fit
        coeffs, cov = optimize.curve_fit(lambda xx, aa, bb, cc: bb * np.sqrt((xx - cc) ** 2 / aa ** 2 + 1.),
                                         x_arr, y_arr, sigma=y_err, p0=p0)

        # return result
        return coeffs[2], cov[2][2]


__all__ = ['AutoFocusProjection']
