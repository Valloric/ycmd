#!/bin/bash

set -ev

YCMD_VENV_DIR=${HOME}/venvs/ycmd_test

# default, may be changed by os-specific
easy_install="easy_install"

echo "Checking for supported OS (travis_install.${TRAVIS_OS_NAME}.sh..."
test -f travis_install.${TRAVIS_OS_NAME}.sh

source travis_install.${TRAVIS_OS_NAME}.sh

# set up a virtualenv for the correct python
sudo $easy_install --upgrade setuptools
sudo $easy_install virtualenv
virtualenv -p python${YCMD_PYTHON_VERSION} ${YCMD_VENV_DIR}
# copy the python-config for the right version into the virtualenv (as ycmd's
# build system requires it, but virtualenv doesn't seem to copy it)
cp /usr/bin/python${YCMD_PYTHON_VERSION}-config ${YCMD_VENV_DIR}/bin/python-config

# this must be done *after* the above copy (for as yet unknown reasons)
set +v
echo "Activate virtualenv..."
source ${YCMD_VENV_DIR}/bin/activate
echo "Done."
set -v

python_version=$(python -c 'import sys; print "{0}.{1}".format( sys.version_info[0], sys.version_info[1] )')
echo "Checking python version (actual $python_version vs expected $YCMD_PYTHON_VERSION)"
test $python_version == $YCMD_PYTHON_VERSION

# install test requirements
pip install -r test_requirements.txt

# typescript required via node.js
npm install -g typescript

# Travis can run out of RAM when compiling if don't prevent parallelization.
export YCM_CORES=1
