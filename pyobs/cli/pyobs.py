import argparse
import os


def init_cli():
    # init argument parsing
    # for all command line parameters we set the default to an environment variable,
    # so they can also be specified that way
    parser = argparse.ArgumentParser()

    # config
    parser.add_argument('config', type=str, help='Configuration file', nargs='?', default=os.environ.get('CONFIG'))

    # logging
    parser.add_argument('--log-level', type=str, choices=['critical', 'error', 'warning', 'info', 'debug'],
                        default=os.environ.get('PYOBS_LOG_LEVEL', 'info'))
    parser.add_argument('-l', '--log-file', type=str, help='file to write log into',
                        default=os.environ.get('PYOBS_LOG_FILE'))
    parser.add_argument('--log-rotate', action='store_true', help='rotate logs automatically',
                        default=os.environ.get('PYOBS_LOG_ROTATE') in ['yes', 'true'])
    parser.add_argument('--fluent-server', type=str, help='Fluent server and port.')

    # debug stuff
    parser.add_argument('--debug-time', type=str, help='Fake time at start for pyobs to use',
                        default=os.environ.get('PYOBS_DEBUG_TIME'))

    # return it
    return parser


def parse_cli(parser: argparse.ArgumentParser):
    from pyobs.utils.time import Time

    # parse args
    args = parser.parse_args()

    # set debug time now
    if args.debug_time is not None:
        # calculate difference between now and given time
        delta = Time(args.debug_time) - Time.now()
        Time.set_offset_to_now(delta)

    # get full path of config
    if args.config:
        args.config = os.path.abspath(args.config)

    # finished
    return vars(args)


def start_daemon(app_class, pid_file=None, *args, **kwargs):
    """Start process as a daemon.

    Args:
        app_class: Class to create app from
        pid_file: Name of PID file.
    """
    import daemon
    from daemon import pidfile

    # get run directory
    run_dir = os.path.dirname(pid_file)

    # This launches the daemon in its context
    with daemon.DaemonContext(
            working_directory=run_dir,
            umask=0o002,
            pidfile=pidfile.TimeoutPIDLockFile(pid_file)) as context:
        run(*args, app_class=app_class, **kwargs)


def run(app_class, **kwargs):
    """Run a pyobs application with the given options.

    Args:
        app_class: Class to create app from
    """

    # create app and run it
    app = app_class(**kwargs)
    app.run()


def main():
    from pyobs.application import Application

    # init argument parsing and add PID/Daemon stuff
    parser = init_cli()
    parser.add_argument('-p', '--pid-file', type=str, default=os.environ.get('PIDFILE'))

    # parse it
    args = parse_cli(parser)

    # run app
    if args['pid_file']:
        start_daemon(app_class=Application, **args)
    else:
        run(app_class=Application, **args)


if __name__ == '__main__':
    main()
