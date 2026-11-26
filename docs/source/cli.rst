Command Line Interface
======================
*pyobs* comes with two different command line tools, :program:`pyobs` and :program:`pyobsd`, which can run a single
module or start multiple ones, respectively.

.. _cli-config-file:

Default parameters via config file
-----------------------------------
Instead of passing parameters on the command line every time, both :program:`pyobs` and :program:`pyobsd` can read
their default values from a YAML config file. The first of the following locations that exists is used:

1. :file:`~/.config/pyobs.yaml`
2. :file:`/etc/pyobs.yaml`
3. :file:`/opt/pyobs/storage/pyobs.yaml`

Within that file, parameters go into a section named after the tool, e.g.::

    pyobs:
      log_level: debug

    pyobsd:
      path: /opt/pyobs
      chuid: pyobs:pyobs

Only a fixed set of parameters can be set this way (roughly those without a value that changes between runs, such as
the module config file itself). Command line parameters always take precedence over values from the config file.
Which config file was picked, if any, is logged on startup.

.. _cli-pyobs:

Module launcher *pyobs*
-----------------------
The :program:`pyobs` command runs a single module. A typical command for running *pyobs* simply defines a configuration
file::

    pyobs config.yaml


Parameters
**********
The command accepts the following optional parameters:

:-h/--help:
    Shows the help for the *pyobs* command.

:--log-level <level>:
    One of critical, error, warning, info, debug. Indicates the level of logging.

:-l/--log-file <file>:
    If provided, in addition to logging to stdout, the log is also written to the given file.

:--log-rotate:
    Only valid in combination with **-l/--log-file**. Requests an automated rotation of log files to avoid
    large files.

:--syslog:
    If given, log messages are also sent to the systemd journal, tagged with the module name.

:-p/--pid-file <file>:
    If given, *pyobs* writes its process ID into the given file and starts in the background.

:--stop-timeout <seconds>:
    How long the shutdown may take after SIGTERM or Ctrl+C, defaults to 30. A module can ask for more time while it
    shuts down (e.g. a cooled camera warming up). If the shutdown takes longer than that, plus a few seconds, the
    module ends itself, so it does not hang even if nobody sends SIGKILL. Further signals during the shutdown are
    ignored. :program:`pyobsd` passes its own **--stop-timeout** here.

:--gui:
    Shows an additional GUI, which is especially useful under Windows, where a graceful exit is otherwise
    impossible.

:--username <username> and --password <password>:
    Username and password for connecting to the central server can be provided here as well as in the given config
    or in environment variables.

:--server <host\:ip>:
    If the server to connect to cannot be inferred from the username, another one can be specified as <host>:<ip>.

:--comm <type>:
    The Comm type to use, if **--username** and **--password** are provided on command line. Must be **xmpp**
    at the moment.


Username and password
*********************
There are three different ways for providing a server connection:

1. Provide it in the config YAML file. It then should have a section like this::

    comm:
      class: pyobs.comm.xmpp.XmppComm
      jid: test@example.com
      password: topsecret

2. Use the **--username** and **--password** command line parameters.

3. Provide the username and password in the environment variables **PYOBS_USERNAME** and **PYOBS_PASSWORD**,
   respectively. The server can be defined via **PYOBS_SERVER**.

.. _cli-pyobsd:

*pyobsd* daemon
---------------
The :program:`pyobsd` command can automatically start and stop multiple modules, if their configuration files are all
stored in a single directory.

Commands
********
There are four basic commands:

:pyobsd start:
    A call to :program:`pyobsd start` starts modules from every single configuration YAML file it can find.
    Every additional parameter limits this to the given module, i.e. :program:`pyobsd start camera` only starts
    the camera module with aconfiguration in **camera.yaml**.

:pyobsd stop:
    Works the same way as :program:`pyobsd start`, but stops the modules. It sends SIGTERM to all of them first, then
    waits for them to exit. A module that is still running after **--stop-timeout** seconds gets SIGKILL, unless it
    asked for more time to shut down (e.g. a cooled camera warming up on close, see
    :class:`~pyobs.mixins.CoolingRampMixin`). In that case pyobsd prints how long it waits and only kills the module
    after that. With **--no-wait**, it only sends SIGTERM and returns immediately. A module that is already shutting
    down does not get SIGTERM again, pyobsd only waits for it. Ctrl+C stops waiting, but not the shutdown: pyobsd
    prints which modules keep shutting down in the background, and **status** shows them as **stopping**. Even then,
    a module ends itself if its shutdown takes too long (see **--stop-timeout** of :program:`pyobs`).
    With **--kill**, it sends SIGKILL right away, also to a module that is already shutting down, e.g. one whose
    shutdown hangs. This cuts a camera's warm-up, so the camera stays cold. A module that is still alive 5 s after
    SIGKILL (stuck in a driver call) keeps its PID file, so that it can't be started a second time.

:pyobsd restart:
    The **restart** command is equivalent to calling first **stop** and then **start**. Since it waits for the stop,
    it can take as long as the warm-up of a cooled camera.
    With **--kill**, it calls **stop --kill** instead of **stop**.

:pyobsd status:
    Gives an overview of detected configuration files and started modules. Each module is **running**, **stopped**,
    or **stopping** (it got SIGTERM and is still shutting down, together with how long it may still take if it asked
    for more time). With **--json**, a stopping module keeps ``"running": true``, since its process is still alive,
    and the ``"state"`` field tells it apart.

:pyobsd setup:
    Sets up the host, see :ref:`cli-pyobsd-setup`.

CLI Parameters
**************
The command accepts the following optional parameters:

:-h/--help:
    Shows the help for the *pyobs* command.

:-c/--config-path <path>:
    Defines the path in which to look for configuration files, defaults to **/opt/pyobs/config**.

:-r/--run-path <path>:
    Defines the path in which to store PID files, defaults to **/opt/pyobs/run**.

:-l/--log-path <path>:
    Defines the path in which to store log files, defaults to **/opt/pyobs/log**. Only used if
    **--file-log** is given.

:--log-level <level>:
    One of critical, error, warning, info, debug. Indicates the level of logging.

:--syslog/--no-syslog:
    Forwards **--syslog** to every started module, so their log messages are also sent to the
    systemd journal. Defaults to enabled.

:--file-log/--no-file-log:
    Forwards **--log-file <log-path>/<module>.log** to every started module, so their log messages
    are also written to a per-module file. Defaults to disabled -- **--syslog** already covers log
    capture under systemd; pass **--file-log** explicitly if you also want (or, without systemd,
    instead need) per-module log files.

:--chuid <user>\:<group>:
    Switches user to the given user in the given group when starting/stopping a module, defaults to **pyobs**.

:--stop-timeout <seconds>:
    How long **stop** and **restart** wait after SIGTERM before sending SIGKILL, defaults to 30. A module can ask for
    more time while it shuts down (it writes the deadline to **<module>.pid.stopping** in the run path). Can also be
    set as **stop_timeout** in the config file.

:--start-stop-daemon <path>:
    The path to the :program:`start-stop-daemon` executable, defaults to **/sbin/start-stop-daemon**.

Note that none of the pathes have to be defined, if the recommended path structure is used.

.. _cli-pyobsd-setup:

Setting up a host
*****************
:program:`pyobsd setup`, run as root, sets up a host for :program:`pyobsd`. It asks for:

1. the mode, **pid** (the systemd mode is not supported by setup yet),
2. the user and group to run the modules as (default **pyobs:pyobs**), and whether to create the user if it doesn't
   exist (with ``adduser --system``, home directory is the base path),
3. the base path (default **/opt/pyobs**),
4. whether to log to the systemd journal (default yes) and to log files (default no).

The default for each question is the current value from the config file, else the built-in default. Then it shows
what it will do and asks before doing it:

- create the user,
- create the directories *config*, *log*, *run* and *storage* in the base path, owned by the user and group, or
  fix their owner (their content is not touched),
- write the answers into the **pyobsd** section of :file:`/etc/pyobs.yaml`. Other sections and other keys in the
  **pyobsd** section keep their values. An existing file is rewritten as plain YAML, so its comments and formatting
  are lost. The old file is copied to :file:`/etc/pyobs.yaml.bak` first.

It warns if a config file earlier in the lookup order (see :ref:`cli-config-file`) exists, e.g.
:file:`~/.config/pyobs.yaml`, since that would be used instead, and if :file:`/opt/pyobs/storage/pyobs.yaml` has a
**pyobsd** section, which is then ignored. It's safe to run it again, it only changes what differs.

Every question has an option. A question given as an option is not asked. With **-y**, or if stdin is not a
terminal, nothing is asked at all, and options not given take their default:

:--mode pid:
    The mode.

:--user <user>[\:<group>]:
    The user and group, the group defaults to the user's name.

:--create-user/--no-create-user:
    Create the user if it doesn't exist. Without **--create-user**, a missing user is an error when nothing is
    asked.

:--path <dir>:
    The base path.

:--syslog/--no-syslog, --file-log/--no-file-log:
    Logging, see above.

:-y/--yes:
    Ask nothing, don't confirm.

:--strict:
    Exit with code 1 on warnings, too. The changes are still made.

The exit code is 0 if the host is set up, and 1 on an error, so a deploy script can check it.
