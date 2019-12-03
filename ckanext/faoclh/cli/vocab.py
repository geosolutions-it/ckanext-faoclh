# -*- coding: utf-8 -*-

import logging
import re
import traceback
import json
import uuid
from datetime import datetime
from pprint import pprint

import ckan.plugins.toolkit as toolkit
from ckan.lib.munge import munge_tag
from ckan.logic.validators import tag_name_validator
from ckan.model.meta import Session
from ckan.model import Package, Group, GroupExtra, Tag, PackageExtra, PackageTag, repo
from ckan.logic import ValidationError
from ckan.lib.navl.dictization_functions import Invalid

from sqlalchemy import and_
from ckan.lib.base import config
from ckan.lib.cli import CkanCommand

DEFAULT_LANG = config.get('ckan.locale_default', 'en')
DATE_FORMAT = '%d-%m-%Y'

log = logging.getLogger(__name__)


class VocabCommand(CkanCommand):
    '''
    A command for working with vocabularies.

    Usage::
     # Loading a vocabulary

     paster --plugin=ckanext-faoclh vocab load --inputfile FILE --config=PATH_TO_INI_FILE

     Where:
       FILE is the local path to a vocab file
       PATH_TO_INI_FILE is the path to the Ckan configuration file
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__

    places_theme_regex = '^ITA_.+'

    _locales_ckan_mapping = {
        'en': 'en',
        'fr': 'fr',
        'es': 'es'
    }

    def __init__(self, name):
        super(VocabCommand, self).__init__(name)

        self.parser.add_option('-i', '--inputfile',
                               dest='vocfile',
                               default=None,
                               help='Path to a JSON file containing the vocabulary to load')
#        self.parser.add_option('--name', dest='name', default=None,
#                               help='Name of the vocabulary to work with')

    def command(self):
        '''
        Parse command line arguments and call appropriate method.
        '''
        try:
            cmd = self.args[0]
        except IndexError:
            print "ERROR: missing command"
            print self.usage
            return

        self._load_config()

        if cmd == 'load':
            self.load()
        # elif cmd == 'initdb':
        #     self.initdb()
        else:
            print(self.usage)
            print('ERROR: Command "%s" not recognized' % (cmd,))
            return

    def load(self):

        vocab_file = self.options.vocfile
        if not(vocab_file):
            print(self.usage)
            print('ERROR: Missing input file')
            return

        print ("Loading vocabulary file {}".format(vocab_file))

        user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
        context = {'user': user['name'], 'ignore_auth': True}

        with open(vocab_file) as json_file:
            data = json.load(json_file)

            vocab_name = data["name"]
            print ("Loaded vocabulary {}".format(vocab_name))

            tags = [{'name':tag['name']} for tag in data['tags']]

            if self._vocab_get(context, vocab_name):
                print("Vocabulary {0} already exists, skipping import.".format(vocab_name))
                # TODO: update vocab by only adding new entries
                return

            vocab = self._vocab_create(context, vocab_name, tags)

            if not(vocab):
                print('ERROR: Vocabulary "%s" not created' % (vocab_name))
                return

        print('Vocabulary successfully loaded ({0})'.format(vocab_name))

    @staticmethod
    def _vocab_get(context, vocab_name):
        try:
            data = {'id': vocab_name}
            return toolkit.get_action('vocabulary_show')(context, data)

        except toolkit.ObjectNotFound:
            return False

    @staticmethod
    def _vocab_create(context, vocab_name, tags):
        print("Creating vocabulary '{0}'".format(vocab_name))

        data = {'name': vocab_name, 'tags': tags}
        vocab = toolkit.get_action('vocabulary_create')(context, data)

        return vocab

    @staticmethod
    def _add_tag(context, vocab, tag):
        print("Adding tag {0} to vocabulary '{1}'".format(tag, vocab['name']))
        data = {'name': tag, 'vocabulary_id': vocab['id']}
        toolkit.get_action('tag_create')(context, data)
