#!/usr/bin/env python

from distutils.core import setup

setup(name='TKperf',
	version='1.2',
	description='TK IO Performance Tests',
	author='Georg Schoenberger',
	author_email='gschoenberger@thomas-krenn.com',
	url='http://git.thomas-krenn.com/TKperf_v1.git',
	package_dir = {'': 'src'},
	packages = ['fio', 'perfTest','plots','reports'],
	package_data  = {'reports':['pics/TKperf_logo.png']},
	scripts = ["scripts/tkperf","scripts/tkperf_dialog.sh","scripts/tkperf-cmp"],
	license = 'GPL'
	)
