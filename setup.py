from setuptools import setup, find_packages
import os

version = '1.0'

setup(
	name='ckanext-faoclh',
	version=version,
	description="FAO CLH extension",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Emanuele Tajariol',
	author_email='etj@geo-solutions.it',
	url='',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.faoclh'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points="""
        [ckan.plugins]
			faoclh=ckanext.faoclh.plugin:FAOCLHGUIPlugin
			
		[paste.paster_command]
        	vocab=ckanext.faoclh.cli.vocab:VocabCommand
			
	""",
	message_extractors={
		'ckanext': [
			('**.py', 'python', None),
			('**.js', 'javascript', None),
			('**/templates/**.html', 'ckan', None),
		],
    }
)
