
import unittest
import subprocess
import os

CITOOL_BIN = os.path.dirname( __file__ ) + '/../bin/citool'

class citool_UTBase ( unittest.TestCase ) :
    def setUp( self ):
        os.chdir( self.TEST_DIR )

    def _call_citool( self, args ) :
        subprocess.check_output( [ CITOOL_BIN ] + args )
        
    def test_tag( self ):
        self._call_citool( [ 'tag', 'branch_A', '--vcsRepo', self.VCS_REPO ] )
        
    def test_tag_ver( self ):
        self._call_citool( [
            'tag', 'branch_A', '1.3.0',
            '--vcsRepo', self.VCS_REPO,
            '--wcDir', 'build_ver' ] )
    