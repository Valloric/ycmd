set python_installer_extension=%YCM_PYTHON_INSTALLER_URL:~-3%

::
:: Python configuration
::

if "%python_installer_extension%" == "exe" (
  curl %YCM_PYTHON_INSTALLER_URL% -o C:\python-installer.exe
  ::C:\python-installer.exe /quiet PrependPath=1 InstallAllUsers=1 Include_launcher=1 InstallLauncherAllUsers=1 Include_test=0 Include_doc=0 Include_dev=1 Include_debug=0 Include_tcltk=0 TargetDir=C:\Python
  C:\python-installer.exe /quiet TargetDir=C:\Python
) else (
  curl %YCM_PYTHON_INSTALLER_URL% -o C:\python-installer.msi
  msiexec /i C:\python-installer.msi TARGETDIR=C:\Python /qn
)

C:\Python\Scripts\pip install -r test_requirements.txt

::
:: Rust configuration
::

curl https://win.rustup.rs/x86_64 -o rustup-init.exe
rustup-init.exe -y

::
:: Go configuration
::

curl https://dl.google.com/go/go1.12.4.windows-amd64.msi -o C:\go-installer.msi
msiexec /i C:\go-installer.msi TARGETDIR=C:\Go /qn
