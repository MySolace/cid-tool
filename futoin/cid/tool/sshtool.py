
import os

from ..runenvtool import RunEnvTool

class sshTool( RunEnvTool ):
    def _installTool( self, env ):
        self._requireDeb(['openssh-client'])
        self._requireRpm(['openssh'])
    
    