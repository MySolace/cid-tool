
import os
import sys

from .cid_utbase import cid_UTBase
from futoin.cid.details.resourcealgo import ResourceAlgo

class cid_deploy_Test( cid_UTBase ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'deploycmd')
    
    @classmethod
    def setUpClass( cls ):
        super(cid_deploy_Test, cls).setUpClass()
        
        os.mkdir(cls.TEST_DIR)
        os.chdir(cls.TEST_DIR)
        
    def test_01_setup(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        self._call_cid(['deploy', 'setup', '--deployDir=setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(cfg['deploy'], {
            'autoServices': {},
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--listen-addr=1.2.3.4'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(cfg['deploy'], {
            'autoServices': {},
            'listenAddress': '1.2.3.4',
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-cpus=3'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(cfg['deploy'], {
            'autoServices': {},
            'maxCpuCount': 3,
            'listenAddress': '1.2.3.4',
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-memory=18M'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(cfg['deploy'], {
            'autoServices': {},
            'maxTotalMemory' : '18M',
            'maxCpuCount': 3,
            'listenAddress': '1.2.3.4',
        })

        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-memory=auto'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(cfg['deploy'], {
            'autoServices': {},
            'maxCpuCount': 3,
            'listenAddress': '1.2.3.4',
        })

        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-cpus=auto'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(cfg['deploy'], {
            'autoServices': {},
            'listenAddress': '1.2.3.4',
        })
        
    def test_02_memdetect_system(self):
        sysmem = int(self._readFile('/proc/meminfo').split()[1])*1024
        ra = ResourceAlgo()
        
        self.assertEqual(sysmem, ra.systemMemory())
        self.assertEqual(sysmem / 2, ra.memoryLimit({}))
    
    def test_02_memdetect_cgroup(self):
        ra = ResourceAlgo()
        
        if os.path.exists('/sys/fs/cgroup/memory/memory.limit_in_bytes'):
            self.assertEqual(sys.maxint, ra.cgroupMemory())
        else:
            self.assertEqual(None, ra.cgroupMemory())
        
        self._writeFile('cgroup_mem', '1234567')
        self.assertEqual(1234567, ra.cgroupMemory('cgroup_mem'))
    
    def test_02_memdetect_config(self):
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-memory=1234M'])
        config = self._readJSON(os.path.join('setupdir', 'futoin.json'))
        self.assertEqual(1234*1024*1024, ResourceAlgo().memoryLimit(config))
        
    def test_03_cpudetect_system(self):
        cpus = self._readFile('/proc/cpuinfo').split("\n")
        cpus = filter(lambda x: x.split(':')[0].strip() == 'processor', cpus)
        cpus = len(list(cpus))
        
        self.assertEqual(cpus, ResourceAlgo().systemCpuCount())

    def test_03_cpudetect_cgroup(self):
        ra = ResourceAlgo()
        
        self._writeFile('cgroup_cpu', '3')
        self.assertEqual(1, ra.cgroupCpuCount('cgroup_cpu'))
        
        self._writeFile('cgroup_cpu', '3-6')
        self.assertEqual(4, ra.cgroupCpuCount('cgroup_cpu'))
        
        self._writeFile('cgroup_cpu', '1,3-6')
        self.assertEqual(5, ra.cgroupCpuCount('cgroup_cpu'))
        
        self._writeFile('cgroup_cpu', '1,3-6,8\n')
        self.assertEqual(6, ra.cgroupCpuCount('cgroup_cpu'))
        
    def test_03_cpudetect_config(self):
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-cpus=132'])
        config = self._readJSON(os.path.join('setupdir', 'futoin.json'))
        self.assertEqual(132, ResourceAlgo().cpuLimit(config))

        
