class Task:
    """Base class for all tasks in the system."""

    def __init__(self, comm: 'Comm' = None, environment: 'Environment' = None, vfs: 'VirtualFileSystem' = None,
                 *args, **kwargs):
        """Initializes a new Task.

        Args:
            comm: Comm object for communicating with other modules.
            environment: The environment to use
            vfs: Virtual File System to use.
        """

        # store variables
        self._comm = comm
        self._environment = environment
        self._vfs = vfs

    @property
    def comm(self):
        """Return the Comm object."""
        return self._comm

    @property
    def environment(self):
        """Return the environment."""
        return self._environment

    @property
    def vfs(self):
        """Return the VFS."""
        return self._vfs

    def name(self):
        """Return name of task."""
        raise NotImplementedError

    def __call__(self):
        """Run the task."""
        raise NotImplementedError


__all__ = ['Task']
