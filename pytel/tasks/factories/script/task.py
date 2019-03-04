import logging


log = logging.getLogger(__name__)


class ScriptTask:
    def __init__(self, filename: str):
        self._filename = filename

    def __call__(self, modules: list):
        # load script
        with open(self._filename, 'r') as f:
            script = f.read()

        # execute it
        try:
            exec(script, modules)
        except:
            log.exception("Error during execution of task:")
