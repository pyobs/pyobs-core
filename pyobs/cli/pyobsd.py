import argparse
import glob
import logging
import os
import subprocess
import sys
import time

log = logging.getLogger('pyobs')


class pyobsDaemon(object):
    def __init__(self, config_path, run_path, log_path, log_level='info',
                 chuid=None, start_stop_daemon='start-stop-daemon'):
        self._config_path = config_path
        self._run_path = run_path
        self._log_path = log_path
        self._log_level = log_level
        self._chuid = chuid
        self._start_stop_daemon = start_stop_daemon

        # find pyobs executable
        filenames = [os.path.abspath(os.path.join(os.path.dirname(__file__), 'pyobs')),
                     '/usr/bin/pyobs', '/usr/local/bin/pyobs']
        for filename in filenames:
            if os.path.exists(filename):
                self._pyobs_exec = filename
                break
        else:
            raise ValueError('Could not find pyobs executable.')

        # get configs and running
        self._configs = self._get_configs()
        self._running = self._get_running()

    def _get_configs(self):
        # get configuration files, ignore those ending on .shared.yaml
        tmp = sorted(glob.glob(os.path.join(self._config_path, '*.yaml')))
        return filter(lambda t: not t.endswith('.shared.yaml'), tmp)

    def _get_running(self):
        # get PID files
        pid_files = sorted(glob.glob(os.path.join(self._run_path, '*.pid')))

        # loop files
        running = []
        for pid_file in pid_files:
            # get pid
            pid = int(self._pid(self._service(pid_file)))

            # check for running
            try:
                os.kill(pid, 0)
            except OSError:
                print('Removing PID file %s without process...' % os.path.basename(pid_file))
                os.remove(pid_file)
            else:
                running.append(pid_file)

        # return running processes
        return running

    def start(self, services=None):
        # get list of running processes
        running = [self._service(r) for r in self._running]
        configs = [self._service(r) for r in self._configs]

        # if no services are given, start all
        if services is None:
            # ignore all configs that start with an underscore, those need to be started explicitly
            services = [self._service(c) for c in configs if not os.path.basename(c).startswith('_')]

        # loop configs
        for service in sorted(services):
            # exists?
            if service not in configs:
                print('Service %s does not exists.' % service)
                sys.exit(1)

            # start it?
            if service in running:
                print('%s already running.' % service)
            else:
                print('Starting %s...' % service)
                self._start_service(service)

    def stop(self, services=None):
        # if no services are given, stop all
        if services is None:
            services = [self._service(r) for r in self._running]

        # loop running and stop them
        for service in services:
            print('Stopping %s...' % service)
            self._stop_service(service)

    def restart(self, services=None):
        # stop all services
        self.stop(services=services)

        # sleep a little and get running
        time.sleep(1)
        self._running = self._get_running()

        # start all services
        self.start(services=services)

    def status(self, services=None):
        # get all configs and running
        configs = [self._service(r) for r in self._configs]
        running = [self._service(r) for r in self._running]

        # if no services are given, get all
        if services is None:
            services = sorted(list(set(configs + running)))

        # print them
        print('cfg run service')
        for p in services:
            print(('[X]' if p in configs else '[ ]') + ' ' + ('[X]' if p in running else '[ ]') + ' ' + p)

    def _start_service(self, service):
        # get PID file
        pid_file = self._pid_file(service)

        # define command
        cmd = []
        cmd.extend([self._start_stop_daemon,
                    '--start',
                    '--quiet',
                    '--pidfile', pid_file])

        # change user?
        if self._chuid:
            cmd.extend(['--chuid', self._chuid])

        # call to pyobs
        cmd.extend(['--exec', self._pyobs_exec,
                    '--',
                    '--pid-file', pid_file,
                    '--log-file', self._log_file(service),
                    '--log-level', self._log_level,
                    self._config_file(service)])

        # execute
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _stop_service(self, service):
        # get service name and PID
        pid_file = self._pid_file(service)

        # stop service
        cmd = [self._start_stop_daemon,
               '--stop', '--quiet', '--oknodo',
               '--pidfile', pid_file]
        if self._chuid:
            cmd.extend(['--user', self._chuid[:self._chuid.find(':')]])
        subprocess.call(cmd)

    @staticmethod
    def _service(config_file):
        # get basename without extension
        return os.path.splitext(os.path.basename(config_file))[0]

    def _config_file(self, service):
        # get pid file
        return os.path.join(self._config_path, service + '.yaml')

    def _pid_file(self, service):
        # get pid file
        return os.path.join(self._run_path, service + '.pid')

    def _log_file(self, service):
        # get pid file
        return os.path.join(self._log_path, service + '.log')

    def _pid(self, service):
        # get pid file
        pid_file = self._pid_file(service)
        if not os.path.exists(pid_file):
            return None

        # get pid
        with open(pid_file, 'r') as f:
            return f.read()


def main():
    # init parser
    parser = argparse.ArgumentParser(description="Daemon for pyobs")
    parser.add_argument('-c', '--config-path', type=str, default='/opt/pyobs/config')
    parser.add_argument('-r', '--run-path', type=str, default='/opt/pyobs/run')
    parser.add_argument('-l', '--log-path', type=str, default='/opt/pyobs/log')
    parser.add_argument('--log-level', type=str, choices=['critical', 'error', 'warning', 'info', 'debug'],
                        default='info')
    parser.add_argument('--chuid', type=str, default='pyobs:pyobs')
    parser.add_argument('--start-stop-daemon', type=str, default='/sbin/start-stop-daemon')
    parser.add_argument('command', type=str, choices=['start', 'stop', 'restart', 'status'])
    parser.add_argument('services', type=str, nargs='*')
    args = parser.parse_args()

    # init daemon
    daemon = pyobsDaemon(args.config_path, args.run_path, args.log_path,
                         log_level=args.log_level, chuid=args.chuid, start_stop_daemon=args.start_stop_daemon)

    # run
    cmd = getattr(daemon, args.command)
    cmd(services=args.services if args.services else None)


if __name__ == '__main__':
    main()
