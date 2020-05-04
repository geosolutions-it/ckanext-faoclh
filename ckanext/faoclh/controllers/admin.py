import logging

import ckan
import ckan.lib.base as base
import ckan.plugins.toolkit as toolkit
import ckanext.multilang.helpers as helpers
from ckan.common import _
from ckan.controllers.admin import AdminController
from ckan.lib.i18n import get_locales_from_config
from ckan.lib.navl.dictization_functions import validate
from ckan.logic import NotFound, ValidationError
from ckan.model import Tag
from ckanext.faoclh.cli.vocab import VocabCommand
from ckanext.multilang.model import TagMultilang
import ckan.lib.base as base

log = logging.getLogger(__name__)


class AdminController(AdminController):
    def __init__(self):
        self.created = False
        self.vocab_name_template_mapper = {
            u'fao_resource_type': u'Resource Type',
            u'fao_activity_type': u'Activity Type',
            u'fao_geographic_focus': u'Geographical Focus'
        }
        self.method_mapper = {
            'GET': self.get,
            'POST': self.post,
        }

        self.errors = []
        self.available_locales = get_locales_from_config()
        user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
        self.context = {'user': user['name'], 'ignore_auth': True}
        self.request = base.request
        self.http_method_handler = self.method_mapper[self.request.method]

    def list_vocabulary_view(self, *args, **kwargs):
        vocab_name = kwargs.get(u'vocabulary_name', u'fao_resource_type')
        vocabulary = self.get_vocab({}, vocab_name)
        localized_tags = TagMultilang.get_all(vocab_name)

        try:
            vocab_label = self.vocab_name_template_mapper[vocab_name]
        except KeyError:
            return base.abort(404)

        context = {
            u'vocab_name': vocab_name,
            u'vocab_label': vocab_label,
            u'tags': vocabulary.get(u'tags', []),
            u'labels': self.format_list_labels(localized_tags, helpers.getLanguage())
        }
        return base.render(u'admin/list_vocabs.html', extra_vars=context)

    def create_vocabularies_view(self, *args, **kwargs):
        return self.http_method_handler(self.request, *args, **kwargs)

    def update_vocabularies_view(self, *args, **kwargs):
        return self.http_method_handler(self.request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        tag_name = request.POST.get(u'tag_name', u'')
        vocab_name = kwargs.get(u'vocabulary_name', u'fao_resource_type')
        tag_id = kwargs.get(u'tag_id', None)
        vocabulary = self.get_vocab({}, vocab_name)

        self.errors = self.get_package_name_validation_errors(tag_name)

        if tag_id:
            self.del_tag(self.context, vocabulary, tag_id)

        result = self.add_tag(vocabulary, tag_name, vocab_name)

        if self.created:
            toolkit.redirect_to('/ckan-admin/vocabulary/edit/{}/tag/{}'.format(
                vocab_name, result))

        try:
            vocab_label = self.vocab_name_template_mapper[vocab_name]
        except KeyError:
            return base.abort(404)

        context = {
            u'vocab_name': vocab_name,
            u'vocab_label': vocab_label,
            u'labels': self.format_labels(localized_tags),
            u'tag_name': tag_name[0] if tag_name else '',
        }

        return base.render(u'admin/edit_create_vocab.html', extra_vars=context)

    def get(self, request, *args, **kwargs):
        vocab_name = kwargs.get(u'vocabulary_name', u'fao_resource_type')
        tag_id = kwargs.get(u'tag_id', None)
        vocabulary = self.get_vocab({}, vocab_name)
        localized_tags = TagMultilang.get_all(vocab_name)

        if tag_id:
            localized_tags = localized_tags.filter(TagMultilang.tag_id == tag_id)

            # if not localized_tags.count():
            #     return base.abort(404)

        tag_name = [tag['display_name']
                    for tag in vocabulary.get('tags', []) if tag['id'] == tag_id]

        try:
            vocab_label = self.vocab_name_template_mapper[vocab_name]
        except KeyError:
            return base.abort(404)

        context = {
            u'vocab_name': vocab_name,
            u'vocab_label': vocab_label,
            u'labels': self.format_labels(localized_tags),
            u'tag_name': tag_name[0] if tag_name else '',
        }

        return base.render(u'admin/edit_create_vocab.html', extra_vars=context)

    def add_tag(self, vocab, tag_name, vocab_name):
        data = {u'name': tag_name, u'vocabulary_id': vocab[u'id']}
        try:
            result = toolkit.get_action(u'tag_create')(self.context, data)
            self.localize_tags(result.get('id'), vocab_name)
            self.created = True
            return result.get('id')
        except ValidationError as e:
            if u'already belongs to vocabulary' in str(e):
                self.errors.append(_(u'Vocabulary tag is already existent.'))
                self.created = False
            return e
        return result

    def localize_tags(self, tag_id, vocab_name):
        labels = [
            {
                u'lang': lang,
                u'text': self.request.POST.get(lang, u''),
                u'name': vocab_name,
                u'id': tag_id,
            }
            for lang in self.available_locales
        ]
        TagMultilang.save_tags(*labels)

    @staticmethod
    def del_tag(context, vocab, tag_name):
        data = {u'id': tag_name, 'vocabulary_id': vocab[u'id']}
        return toolkit.get_action(u'tag_delete')(context, data)

    @staticmethod
    def get_package_name_validation_errors(package_name):
        context = {u'model': ckan.model, u'session': ckan.model.Session}
        schema = ckan.logic.schema.default_create_package_schema()

        data_dict = {u'name': package_name}
        data, errors = validate(data_dict, schema, context)
        return errors.get(u'name', [])

    @staticmethod
    def get_vocab(context, vocab_name):
        try:
            data = {u'id': vocab_name}
            return toolkit.get_action(u'vocabulary_show')(context, data)

        except toolkit.ObjectNotFound:
            return {}

    @staticmethod
    def format_labels(labels):
        label_dict = {}
        for label in labels:
            label_dict[label.lang] = label.text
        return label_dict

    @staticmethod
    def format_list_labels(labels, lang):
        label_dict = {}
        for label in labels.filter(TagMultilang.lang == lang):
            label_dict[label.tag_id] = label.text
        return label_dict
