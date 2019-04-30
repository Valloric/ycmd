# Exit immediately if a command returns a non-zero status.
set -e

#
# Python setup
#

brew install pyenv

eval "$(pyenv init -)"

# In order to work with ycmd, Python *must* be built as a shared library. The
# most compatible way to do this on macOS is with --enable-framework. This is
# set via the PYTHON_CONFIGURE_OPTS option.
PYTHON_CONFIGURE_OPTS="--enable-framework" \
pyenv install ${YCM_PYTHON_VERSION}
pyenv global ${YCM_PYTHON_VERSION}

pip install -r test_requirements.txt

#
# Rust setup
#

curl https://sh.rustup.rs -sSf | sh -s -- -y

set +e
