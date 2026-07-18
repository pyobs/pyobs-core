from pyobs.utils import exceptions as exc


class ScriptError(exc.PyobsError):
    """A script failed while running -- e.g. a proxy/network failure reaching a module it depends
    on. Deliberately a single flat type rather than per-script leaves; mint a more specific one
    only once a caller actually wants to distinguish a script's failure modes."""

    pass


__all__ = ["ScriptError"]
