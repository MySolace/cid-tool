
from ..runenvtool import RunEnvTool

class curlTool( RunEnvTool ):
    def _installTool( self, env ):
        self._requirePackages(['curl'])
