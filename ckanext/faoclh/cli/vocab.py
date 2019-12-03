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
        self.parser.add_option('-n', '--name', dest='name', default=None,
                              help='Name of the vocabulary to work with')

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
        elif cmd == 'delete':
            self.delete()
        else:
            print(self.usage)
            print('ERROR: Command "%s" not recognized' % (cmd,))
            return

    def delete(self):
        vocab_name = self.options.name
        if not(vocab_name):
            print(self.usage)
            print('ERROR: Missing vocabulary name')
            return

        print ("Removing vocabulary {}".format(vocab_name))
        user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
        context = {'user': user['name'], 'ignore_auth': True}

        vocab = self._vocab_get(context, vocab_name)
        if not(vocab):
            print("Vocabulary {0} does not exists.".format(vocab_name))
            return

        data = {'vocabulary_id': vocab_name}
        tags = toolkit.get_action('tag_list')(context, data)
        for tag in tags:
            self._del_tag(context, vocab, tag)

        data = {'id': vocab['id']}
        return toolkit.get_action('vocabulary_delete')(context, data)

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
            loaded_tags = data['tags']
            tag_names = [tag['name']  for tag in loaded_tags]

            print ("Loaded vocabulary {}".format(vocab_name))

            vocab = self._vocab_get(context, vocab_name)
            if vocab:
                print("Vocabulary {0} already exists.".format(vocab_name))
                ret = self._vocab_update(context, vocab, tag_names)
            else:
                ret = self._vocab_create(context, vocab_name, tag_names)

        print('Vocabulary successfully loaded ({0})'.format(vocab_name))

    @staticmethod
    def _vocab_get(context, vocab_name):
        try:
            data = {'id': vocab_name}
            return toolkit.get_action('vocabulary_show')(context, data)

        except toolkit.ObjectNotFound:
            return False

    @staticmethod
    def _tags_get(context, vocab_name):
        try:
            data = {'vocabulary_id': vocab_name}
            return toolkit.get_action('tag_list')(context, data)

        except toolkit.ObjectNotFound:
            return False

    @staticmethod
    def _vocab_create(context, vocab_name, tags):
        print("Creating vocabulary '{0}'".format(vocab_name))

        tags_list_dict = [{'name': tag} for tag in tags]
        data = {'name': vocab_name, 'tags': tags_list_dict}
        vocab = toolkit.get_action('vocabulary_create')(context, data)

        return vocab

    def _vocab_update(self, context, vocab, tags):
        vocab_name = vocab['name']
        print("Updating vocabulary '{0}'".format(vocab_name))

        data = {'vocabulary_id': vocab_name}
        old_tags = toolkit.get_action('tag_list')(context, data)

        to_add = [tag for tag in tags if tag not in old_tags]
        to_del = [tag for tag in old_tags if tag not in tags]

        print("Tags to add '{}'".format(to_add))
        print("Tags to remove '{}'".format(to_del))

        for tag in to_add:
            self._add_tag(context, vocab, tag)

        for tag in to_del:
            self._del_tag(context, vocab, tag)

        return True

    def _add_tag(self, context, vocab, tag_name):
        vocab_name = vocab['name']
        print("Adding tag {1} : {0}".format(tag_name, vocab_name))
        data = {'name': tag_name, 'vocabulary_id': vocab['id']}
        return toolkit.get_action('tag_create')(context, data)

    def _del_tag(self, context, vocab, tag_name):
        vocab_name = vocab['name']
        print("Removing tag {1} : {0}".format(tag_name, vocab_name))
        data = {'id': tag_name, 'vocabulary_id': vocab['id']}
        return toolkit.get_action('tag_delete')(context, data)
