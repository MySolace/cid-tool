#!/bin/bash

if ! test -e bin/cid; then
    echo "Invoke from CITool project root!"
    exit 1
fi

CID_BOOT=$(pwd)/bin/cid

if [ "$1" = 'fast' ]; then
    fast=fast
    shift 1
fi

if [ "$1" = 'frompip' ]; then
    pythonVer='2' $CID_BOOT tool exec pip -- install --upgrade futoin-cid
    pythonVer='3' $CID_BOOT tool exec pip -- install --upgrade futoin-cid
    shift 1
    
    fast=fast
else
    pythonVer='2' $CID_BOOT tool exec pip -- install -e $(pwd)
    pythonVer='3' $CID_BOOT tool exec pip -- install -e $(pwd)
fi

if [ "$1" = 'nocompile' ]; then
    export CIDTEST_NO_COMPILE=1
    shift 1
else
    unset CIDTEST_NO_COMPILE
fi


if [ -z "$1" ]; then
    tests=
    tests+=" tests/citool_tools_test.py"
    tests+=" tests/citool_git_test.py"
    tests+=" tests/citool_hg_test.py"
    tests+=" tests/citool_svn_test.py"
else
    tests="$*"
fi

# CentOS 6
[ -e /opt/rh/python27/enable ] && source /opt/rh/python27/enable 

if [ "$fast" != 'fast' ]; then
    echo "Python 3"
    (
        eval $(pythonVer='3' $CID_BOOT tool env virtualenv)
        export CIDTEST_BIN=$(which cid)

        pythonVer='3' $CIDTEST_BIN tool exec pip -- install nose
        pythonVer='3' $CIDTEST_BIN tool exec python -- -m nose $tests
    )
fi

echo "Python 2"
(
    eval $(pythonVer='2' $CID_BOOT tool env virtualenv)
    export CIDTEST_BIN=$(which cid)
    pythonVer='2' $CIDTEST_BIN tool exec pip -- install nose
    pythonVer='2' $CIDTEST_BIN tool exec python -- -m nose $tests
)