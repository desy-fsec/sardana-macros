#!/usr/bin/env python

from distutils.core import setup
from distutils.sysconfig import *
import os, sys, string

installs=[]
data=[]


for root, dirs, files in os.walk('python/'):
	for name in files:
		if not name.endswith(".py"):
			data.append([get_python_lib() + '/' + root, [root + '/' + name]])
	for dir in dirs:
		installs.append(root + '/' + dir)

setup(name='sardana-macros',
	version='2020.01.29',
	description='sardana python macros',
	author='several',
	url='//git.code.sf.net/u/tere29/sardanacontrollers',
	packages=installs,
	data_files=data
	)
