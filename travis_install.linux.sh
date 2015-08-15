# Linux-specific installation
sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
sudo add-apt-repository -y ppa:ermshiperete/monodevelop
sudo add-apt-repository -y ppa:fkrull/deadsnakes

sudo apt-get -qq update
sudo apt-get -qq install python${YCMD_PYTHON_VERSION} python${YCMD_PYTHON_VERSION}-dev
sudo apt-get -qq install python-setuptools

sudo apt-get -qq install monodevelop-current
sudo apt-get -qq install g++-4.8
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.8 90
MONO_PREFIX=/opt/monodevelop
export DYLD_LIBRARY_FALLBACK_PATH=$MONO_PREFIX/lib:$DYLD_LIBRARY_FALLBACK_PATH
export LD_LIBRARY_PATH=$MONO_PREFIX/lib:$LD_LIBRARY_PATH
export C_INCLUDE_PATH=$MONO_PREFIX/include:$C_INCLUDE_PATH
export PKG_CONFIG_PATH=$MONO_PREFIX/lib/pkgconfig:$PKG_CONFIG_PATH
export PATH=$MONO_PREFIX/bin:$PATH
