
from __future__ import print_function, absolute_import

import os
import sys
import subprocess
import glob
from ..coloring import Coloring


class PathMixIn(object):
    _dev_null = None

    def _callExternal(self, cmd, suppress_fail=False, verbose=True, output_handler=None, input=False):
        try:
            if not PathMixIn._dev_null:
                PathMixIn._dev_null = open(os.devnull, 'w')

            if input:
                stdin = subprocess.PIPE
            else:
                stdin = PathMixIn._dev_null

            if verbose and not suppress_fail:
                print(Coloring.infoLabel('Call: ') +
                      Coloring.info(subprocess.list2cmdline(cmd)),
                      file=sys.stderr)
                stderr = sys.stderr
            else:
                stderr = PathMixIn._dev_null

            if output_handler:
                chunk_size = 65536
                p = subprocess.Popen(cmd, stdin=stdin, stderr=stderr,
                                     bufsize=chunk_size * 2, close_fds=True,
                                     stdout=subprocess.PIPE)

                try:
                    while True:
                        chunk = p.stdout.read(chunk_size)

                        if chunk:
                            output_handler(chunk)
                        else:
                            break
                finally:
                    p.wait()

                if p.returncode != 0:
                    raise subprocess.CalledProcessError(
                        'Failed {0}'.format(p.returncode))

                return True

            elif input:
                p = subprocess.Popen(cmd, stdin=stdin, stderr=stderr,
                                     bufsize=4096, close_fds=True,
                                     stdout=subprocess.PIPE)

                try:
                    p.stdin.write(input)
                finally:
                    p.wait()

                if p.returncode != 0:
                    raise subprocess.CalledProcessError(
                        'Failed {0}'.format(p.returncode))

                return True

            else:
                res = subprocess.check_output(cmd, stdin=stdin, stderr=stderr)

                try:
                    res = str(res, 'utf8')
                except:
                    pass

                return res
        except subprocess.CalledProcessError:
            if suppress_fail:
                return None
            raise

    def _callInteractive(self, cmd, replace=True):
        if replace:
            print(Coloring.infoLabel('Exec: ') +
                  Coloring.info(subprocess.list2cmdline(cmd)),
                  file=sys.stderr)

            sys.stdout.flush()
            sys.stderr.flush()
            os.execv(cmd[0], cmd)
        else:
            print(Coloring.infoLabel('Call: ') +
                  Coloring.info(subprocess.list2cmdline(cmd)),
                  file=sys.stderr)
            sys.stdout.flush()
            sys.stderr.flush()

            return subprocess.check_call(cmd)

    def _trySudoCall(self, cmd, errmsg=None):
        try:
            self._callExternal(['sudo', '-n'] + cmd)
        except subprocess.CalledProcessError:
            if not errmsg:
                errmsg = 'you may need to call the the failed command manually !'

            self._warn(errmsg)

    def _which(self, program):
        "Copied from stackoverflow"
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

        return None

    def _addEnvPath(self, env_name, add_dir, first=False):
        if env_name in os.environ:
            dir_list = os.environ[env_name].split(os.pathsep)
        else:
            dir_list = []

        if add_dir not in dir_list:
            if first:
                dir_list[0:0] = [add_dir]
            else:
                dir_list.append(add_dir)

            os.environ[env_name] = os.pathsep.join(dir_list)

    def _addBinPath(self, bin_dir, first=False):
        self._addEnvPath('PATH', bin_dir, first=first)

    def _addPackageFiles(self, config, pattern):
        files = glob.glob(pattern)

        if not files:
            self._errorExit(
                'Failed to find created packages of "{0}" pattern'.format(pattern))

        config.setdefault('packageFiles', [])
        config['packageFiles'] += files
