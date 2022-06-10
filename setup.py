#!/usr/bin/env python

# import os
# import imp
from setuptools import setup

release = "1.0.2"

package_dir = {"sardana.sardana-macros.DESY_general": "DESY_general"}

packages = ["sardana.sardana-macros.DESY_general"]

provides = ['python']


setup(name='sardana-macros',
      version=release,
      author="Sardana Controller Developers",
      author_email="fs-ec@desy.de",
      maintainer="DESY",
      maintainer_email="fs-ec@desy.de",
      url="https://sourceforge.net/u/tere29/sardanamacros/ci/master/tree/",
      packages=packages,
      package_dir=package_dir,
      include_package_data=True,
      provides=provides,
      )
