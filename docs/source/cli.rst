Command Line Interface
======================
*pyobs* comes with two different command line tools, :program:`pyobs` and :program:`pyobsd`, which can run a single
module or start multiple ones, respectively.

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

:-p/--pid-file <file>:
    If given, *pyobs* writes its process ID into the given file and starts in the background.

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
    Works the same way as :program:`pyobsd start`, but stops the modules.

:pyobsd restart:
    The **restart** command is equivalent to calling first **stop** and then **start**

:pyobsd status:
    Gives an overview of detected configuration files and started modules.

CLI Parameters
**************
The command accepts the following optional parameters:

:-h/--help:
    Shows the help for the *pyobs* command.

:-c/--config-path <path>:
    Defines the path in which to look for configuration files, defaults to **/opt/pyobs/config**.

:-r/--run-path <path>:
    Defines the path in which to store PID files, defaults to **/opt/pyobs/run**.

:-r/--run-path <path>:
    Defines the path in which to store log files, defaults to **/opt/pyobs/log**.

:--log-level <level>:
    One of critical, error, warning, info, debug. Indicates the level of logging.

:--chuid <user>\:<group>:
    Switches user to the given user in the given group when starting/stopping a module.

:--start-stop-daemon <path>:
    The path to the :program:`start-stop-daemon` executable, defaults to **/sbin/start-stop-daemon**.

Note that none of the pathes have to be defined, if the recommended path structure is used.