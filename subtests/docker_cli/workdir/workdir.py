r"""
Summary
---------

Test that checks the ``docker run --workdir`` command could set workdir
successfully if the dir is a valid path, and fails if it's not absolute path or
not a path, like a file.

Operational Summary
----------------------

#. Run container w/ valid & invalid workdir
#. Verify access or failure is as expected

Operational Detail
-------------------

Positive test
~~~~~~~~~~~~~~~
#. Run a container with an existing workdir
#. Run a container with an non-existing workdir

Negative testing
~~~~~~~~~~~~~~~~~~
#. Run a container with an invalid workdir which is not absolute path
#. Run a container with the workdir which is not a path, but a file

Prerequisites
-------------------------------------
*  Docker daemon is running and accessible by it's unix socket.
"""

from autotest.client import utils
from dockertest import subtest
from dockertest.output import mustpass
from dockertest.dockercmd import DockerCmd
from dockertest.images import DockerImage
from dockertest.output import OutputGood


class workdir(subtest.Subtest):

    def initialize(self):
        super(workdir, self).initialize()
        self.stuff['fin'] = DockerImage.full_name_from_defaults(self.config)
        _path = utils.generate_random_string(12)
        self.stuff['good_dirs'] = {}
        self.stuff['good_dirs']['exist_dir'] = '/var/log'
        self.stuff['good_dirs']['nonexist_dir'] = '/tmp/%s' % _path
        self.stuff['bad_dirs'] = {}
        self.stuff['bad_dirs']['invalid_dir'] = 'tmp/%s' % _path
        self.stuff['bad_dirs']['file_as_dir'] = '/etc/hosts'
        self.stuff['cmdresults'] = {}

    def run_once(self):
        super(workdir, self).run_once()
        for name, _dir in self.stuff['good_dirs'].items():
            subargs = ['--workdir=%s' % _dir]
            subargs.append('--name=%s' % name)
            subargs.append(self.stuff['fin'])
            subargs.append('pwd')
            nfdc = DockerCmd(self, 'run', subargs)
            self.stuff['cmdresults'][name] = mustpass(nfdc.execute())
        for name, _dir in self.stuff['bad_dirs'].items():
            subargs = ['--workdir=%s' % _dir]
            subargs.append('--name=%s' % name)
            subargs.append(self.stuff['fin'])
            subargs.append('pwd')
            dc = DockerCmd(self, 'run', subargs)
            self.stuff['cmdresults'][name] = dc.execute()

    def postprocess(self):
        super(workdir, self).postprocess()
        for name, _dir in self.stuff['good_dirs'].items():
            _command = self.stuff['cmdresults'][name].command
            self.logdebug("Commands: %s" % _command)
            self.failif_ne(self.stuff['cmdresults'][name].stdout.strip(), _dir,
                           "failed to set workdir")
            self.logdebug("workdir %s set successful for container" % _dir)
        for name, _dir in self.stuff['bad_dirs'].items():
            _command = self.stuff['cmdresults'][name].command
            self.logdebug("Commands: %s" % _command)
            outputgood = OutputGood(self.stuff['cmdresults'][name],
                                    ignore_error=True)
            self.failif(self.stuff['cmdresults'][name].exit_status == 0,
                        str(outputgood))
            if self.stuff['cmdresults'][name].exit_status != 0:
                self.logdebug("Intend to fail:\n %s" %
                              self.stuff['cmdresults'][name].stderr.strip())

    def cleanup(self):
        super(workdir, self).cleanup()
        if self.config['remove_after_test']:
            containers = [name for name in self.stuff['good_dirs'].keys()]
            dkrcmd = DockerCmd(self, 'rm', containers)
            dkrcmd.execute()
            containers = [name for name in self.stuff['bad_dirs'].keys()]
            dkrcmd = DockerCmd(self, 'rm', containers)
            dkrcmd.execute()
