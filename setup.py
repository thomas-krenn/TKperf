#!/usr/bin/env python3

from distutils.core import setup

setup(name='TKperf',
	version='2.2',
	description='TKperf - Thomas Krenn IO Performance Tests',
	author='Georg Schoenberger',
	author_email='g.schoenberger@xortex.com',
	url='https://github.com/thomas-krenn/TKperf.git',
	package_dir = {'': 'src'},
	packages = ['fio', 'perfTest','plots','reports','system'],
	package_data  = {'reports':['pics/TKperf_logo.png']},
	scripts = ["scripts/tkperf","scripts/tkperf-cmp"],
	license = 'GPL'
	)
