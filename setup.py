#!/usr/bin/env python

from distutils.core import setup

setup(name='TKperf',
	version='2.1',
	description='TKperf - Thomas Krenn IO Performance Tests',
	author='Georg Schoenberger',
	author_email='gschoenberger@thomas-krenn.com',
	url='https://github.com/thomas-krenn/TKperf_v1.git',
	package_dir = {'': 'src'},
	packages = ['fio', 'perfTest','plots','reports','system'],
	package_data  = {'reports':['pics/TKperf_logo.png']},
	scripts = ["scripts/tkperf","scripts/tkperf-cmp"],
	license = 'GPL'
	)
