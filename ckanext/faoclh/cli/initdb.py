import logging
import re
import sys

from ckan.lib.cli import CkanCommand
from ckan.lib.helpers import json

log = logging.getLogger(__name__)


class InitializeDatabaseTables(CkanCommand):
    '''Initializes all database tables needed bu ckanext-faoclh.

    Usage:
        faoclh initdb []
            Creates the necessary tables.

    The commands should be run from the ckanext-faoclh directory and expect
    a development.ini file to be present. Most of the time you will
    specify the config explicitly though::

        paster extents update --config=../ckan/development.ini

    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 2
    min_args = 0

    def command(self):
        self._load_config()
        from ckanext.faoclh.model.tag_image_url import setup as db_setup
        db_setup()
