import sys
import platform
from setuptools import setup, find_packages

data_files_to_install = []

python_ver = platform.python_version().rsplit(".", 1)[0]

if sys.platform == 'linux':
    # Code to run only on Linux
    print("Building for Linux...")
    data_files_to_install.append((f"lib/python{python_ver}/site-packages/targets",
                                  ["src/targets/Qleo.yml"]))
    data_files_to_install.append((f"lib/python{python_ver}/site-packages/lib",
                                  ["src/lib/libnvqir-Qleo.so"]))
    data_files_to_install.append((f"lib/python{python_ver}/site-packages/targets",
                                  ["src/targets/QleoGPU.yml"]))
    data_files_to_install.append((f"lib/python{python_ver}/site-packages/lib",
                                  ["src/lib/libnvqir-QleoGPU.so"]))

setup(
    name="qleo",
    version="0.1",
    packages=["qleo"],
    package_dir={"qleo": "src/qleo"},
    include_package_data=True,
    data_files=data_files_to_install,
)
