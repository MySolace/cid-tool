
import os
import subprocess
from ..mixins.util import UtilMixIn


class ResourceAlgo(UtilMixIn):
    def systemMemory(self):
        try:
            return os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        except ValueError:
            if self._isMacOS():
                return int(subprocess.check_output(['sysctl', '-n', 'hw.memsize']).strip())
            else:
                self._errorExit('Failed to detect system memory size')

    def cgroupMemory(self, cgroupFile=None):
        cgroupFile = cgroupFile or '/sys/fs/cgroup/memory/memory.limit_in_bytes'

        if os.path.exists(cgroupFile):
            return int(self._readTextFile(cgroupFile).strip())

        return None

    def memoryLimit(self, config):
        maxTotalMemory = config.get('deploy', {}).get('maxTotalMemory', None)

        if maxTotalMemory:
            return self._parseMemory(maxTotalMemory)

        sysMem = self.systemMemory()
        cgroupMem = self.cgroupMemory()

        if cgroupMem and cgroupMem < sysMem:
            return cgroupMem
        else:
            return sysMem / 2

    def systemCpuCount(self):
        return min(os.sysconf('SC_NPROCESSORS_ONLN'), os.sysconf('SC_NPROCESSORS_CONF'))

    def cgroupCpuCount(self, cgroupFile=None):
        cgroupFile = cgroupFile or '/sys/fs/cgroup/cpuset/cpuset.cpus'

        if not os.path.exists(cgroupFile):
            return None

        cpus = self._readTextFile(cgroupFile).strip()
        cpus = cpus.split(',')
        count = 0

        for c in cpus:
            c = c.split('-')

            if len(c) == 2:
                count += len(range(int(c[0]), int(c[1]) + 1))
            else:
                count += 1

        return count

    def cpuLimit(self, config):
        maxCpuCount = config.get('deploy', {}).get('maxCpuCount', None)

        if maxCpuCount:
            return maxCpuCount

        cpu_count = self.systemCpuCount()
        cgroup_count = self.cgroupCpuCount()

        if cgroup_count:
            return min(cpu_count, cgroup_count)
        else:
            return cpu_count

    def configServices(self, config):
        memLimit = self.memoryLimit(config)
        cpuLimit = self.cpuLimit(config)

        self.distributeResources(config, memLimit, cpuLimit)
        self.assignSockets(config)

    def distributeResources(self, config, maxmem, maxcpu, granularity=1024):
        maxmem /= granularity
        availMem = maxmem
        deploy = config.setdefault('deploy', {})
        autoServices = deploy.setdefault('autoServices', {})
        entryPoints = config.get('entryPoints', {})

        services = {}
        candidates = set()
        debug = (config.get('env', {}).get('type', 'dev') == 'dev')

        # Init
        for (en, ei) in entryPoints.items():
            ei = ei.copy()

            for f in ('minMemory', 'connMemory'):
                if f not in ei:
                    self._errorExit(
                        '"{0}" is missing from {1} entry point'.format(f, en))
                ei[f] = self._parseMemory(ei[f]) / granularity

            for f in ('maxMemory', 'maxTotalMemory', 'debugOverhead', 'debugConnOverhead'):
                if f in ei:
                    ei[f] = self._parseMemory(ei[f]) / granularity

            ei.setdefault('memWeight', 100)
            ei.setdefault('cpuWeight', 100)
            ei.setdefault('maxMemory', maxmem)
            ei.setdefault('maxTotalMemory', maxmem)
            ei.setdefault('scalable', True)
            ei.setdefault('multiCore', True)
            ei.setdefault('reloadable', False)

            if debug:
                ei['minMemory'] += ei.get('debugOverhead', 0)
                ei['connMemory'] += ei.get('debugConnOverhead', 0)

            if (not ei['scalable']) and ei['maxMemory'] < ei['maxTotalMemory']:
                ei['maxTotalMemory'] = ei['maxMemory']

            ei['instances'] = 1
            ei['memAlloc'] = ei['minMemory']
            availMem -= ei['minMemory']

            services[en] = ei
            candidates.add(en)

        if availMem < 0:
            self._errorExit(
                'Not enough memory to allocate services: deficit "{0}" bytes'.format(availMem))

        # Distribute remaining
        while availMem > 0 and len(candidates) > 0:
            overall_weight = 0

            for en in candidates:
                overall_weight += services[en]['memWeight']

            distMem = availMem
            to_del = set()

            for en in candidates:
                ei = services[en]
                memAlloc = ei['memAlloc']
                addAlloc = distMem * ei['memWeight'] / overall_weight

                if (memAlloc + addAlloc) > ei['maxTotalMemory']:
                    ei['memAlloc'] = ei['maxTotalMemory']
                    addAlloc = ei['memAlloc'] - memAlloc
                    to_del.add(en)

                availMem -= addAlloc

            candidates -= to_del

            if availMem == distMem:
                break

        # Distribute instances
        min_mem_coeff = 2

        for (en, ei) in services.items():
            if not ei['scalable']:
                continue

            reasonableMinMemory = ei['minMemory'] * min_mem_coeff

            if ei['multiCore']:
                if (not ei['reloadable']) and ei['memAlloc'] >= (reasonableMinMemory * 2):
                    ei['instances'] = 2
            else:
                possible_instances = ei['memAlloc'] / reasonableMinMemory

                if ei['reloadable'] or maxcpu > 1:
                    ei['instances'] = min(maxcpu, possible_instances)
                else:
                    ei['instances'] = min(2, possible_instances)

            ei['instances'] = min(ei['instances'], ei.get(
                'maxInstances', ei['instances']))

        # create services
        for (en, ei) in services.items():
            instances = []
            instance_count = ei['instances']
            service_mem = 0

            for i in range(0, instance_count):
                ic = {}
                instance_mem = ei['memAlloc'] / instance_count
                ic['maxMemory'] = instance_mem
                service_mem += instance_mem
                instances.append(ic)

            instances[0]['maxMemory'] += (ei['memAlloc'] - service_mem)

            for ic in instances:
                ic['maxClients'] = (
                    ic['maxMemory'] - ei['minMemory']) / ei['connMemory']

            autoServices[en] = instances

    def assignSockets(self, config):
        port = 1025
        deploy = config.setdefault('deploy', {})
        autoServices = deploy.setdefault('autoServices', {})
        entryPoints = config.get('entryPoints', {})

        base_dir = os.path.realpath(config['deployDir'])
        run_dir = os.path.join(base_dir, 'run')
        run_dir = config.get('env', {}).get('runDir', run_dir)

        for (en, instances) in autoServices.items():
            ei = entryPoints[en]

            for i in range(0, len(instances)):
                ic = instances[i]

                socket_types = ei.get('socketTypes', ['unix'])
                sock_type = ei.get('socketType', socket_types[0])

                ic['socketType'] = sock_type

                if sock_type == 'unix':
                    ic['socketPath'] = os.path.join(
                        run_dir, '{0}.{1}.sock'.format(en, i))
                else:
                    ic['socketAddr'] = deploy.get('listenAddress', '0.0.0.0')
                    ic['socketPort'] = ei.get('socketPort', port)
                    port += 1
