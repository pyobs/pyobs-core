class Task:
    """Base class for all tasks in the system."""

    def __init__(self, comm: 'Comm' = None, observer: 'Observer' = None, vfs: 'VirtualFileSystem' = None,
                 *args, **kwargs):
        """Initializes a new Task.

        Args:
            comm: Comm object for communicating with other modules.
            observer: The observer to use
            vfs: Virtual File System to use.
        """

        # store variables
        self._comm = comm
        self._observer = observer
        self._vfs = vfs

    @property
    def comm(self):
        """Return the Comm object."""
        return self._comm

    @property
    def observer(self):
        """Return the observer."""
        return self._observer

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
