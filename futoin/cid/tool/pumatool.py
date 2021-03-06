#
# Copyright 2015-2017 (c) Andrey Galkin
#


from ..runtimetool import RuntimeTool
from .bundlermixin import BundlerMixIn


class pumaTool(BundlerMixIn, RuntimeTool):
    """A ruby web server built for concurrency http://puma.io

NOTE: the tool can only be used in scope of Ruby project through
bundler
"""
    __slots__ = ()

    def _sigReload(self):
        return self._ext.signal.SIGUSR2

    def getDeps(self):
        return ['bundler']

    def tuneDefaults(self, env):
        return {
            'minMemory': '128M',
            'connMemory': '8M',
            'connFD': 8,
            'socketTypes': ['unix', 'tcp'],
            'socketType': 'unix',
            'socketProtocol': 'http',
            'scalable': True,
            'reloadable': True,
            'multiCore': False,  # use workers on service level
            'maxRequestSize': '1M',
        }

    def onRun(self, config, svc, args):
        svc_tune = svc['tune']

        #---

        if svc_tune['socketType'] == 'unix':
            socket = 'unix://{0}'.format(svc_tune['socketPath'])
        else:
            socket = 'tcp://{0}:{1}'.format(
                svc_tune['socketAddress'], svc_tune['socketPort'])

        #---
        resource = self._ext.resource
        heap_limit = self._configutil.parseMemory(svc_tune['maxMemory'])
        # both limit RAM and HEAP (not the same)
        resource.setrlimit(resource.RLIMIT_RSS, (heap_limit, heap_limit))
        resource.setrlimit(resource.RLIMIT_DATA, (heap_limit, heap_limit))

        #---
        threads = svc_tune['maxConnections']

        puma_args = [
            '-b', socket,
            '-e', self._environ['RUBY_ENV'],
            '-t', '{0}:{0}'.format(threads),
            '--dir', self._os.getcwd(),  # force chdir() on reload
        ]

        #---
        env = config['env']

        cmd = [
            env['bundlerBin'],
            'exec', env['pumaBin'],
            svc['path']
        ] + puma_args + args

        self._ensureInstalled(env)
        self._executil.callInteractive(cmd)
