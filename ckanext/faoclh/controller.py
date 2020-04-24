import logging

import ckan
import ckan.lib.base as base
import ckan.plugins.toolkit as toolkit
from ckan.common import _
from ckan.lib.navl.dictization_functions import validate
from ckan.logic import NotFound, ValidationError
from ckanext.faoclh.cli.vocab import VocabCommand
from ckan.lib.i18n import get_locales_from_config
import ckanext.multilang.helpers as helpers
from ckanext.multilang.model import TagMultilang
from ckan.model import Tag
from ckanext.multilang.model import TagMultilang

log = logging.getLogger(__name__)


class VocabularyController(base.BaseController):
    def __init__(self):
        self.created = False
        self.template_mapper = {
            u'fao_resource_type': u'Resource Type',
            u'fao_activity_type': u'Activity Type',
            u'fao_geographic_focus': u'Geographical Focus'
        }
        self.errors = []
        self.available_locales = get_locales_from_config()
        user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
        self.context = {'user': user['name'], 'ignore_auth': True}

    def vocabularies(self, *args, **kwargs):
        self.request = kwargs[u'pylons'].request
        self.name = self.request.POST.get(u'name', u'')
        self.lang = helpers.getLanguage()
        self.vocab_name = self.request.GET.get(u'vocab_name', u'fao_resource_type')
        self.tag = self.request.GET.get(u'tag', u'')
        self.vocabs = self.get_vocab({}, self.vocab_name)
        success = self.request.GET.get('success', 'false')

        all_labels = TagMultilang.get_all(self.vocabs[u'name'])
        if self.tag and self.tag != 'NEW':
            all_labels = all_labels.filter(TagMultilang.tag_id == self.tag)
        tag_name = [tag['display_name'] for tag in self.vocabs.get('tags', []) if tag['id'] == self.tag]

        if self.url_errors():
            return base.abort(404)

        if self.request.method == u'POST':
            self.errors = self.get_package_name_validation_errors(self.name)

            if not self.errors:
                if self.tag != u'NEW':
                    self.del_tag(self.context, self.vocabs, self.tag)

                result = self.add_tag(self.vocabs, self.name)

                if self.created:
                    toolkit.redirect_to('/{}/ckan-admin/vocabs?vocab_name={}&tag={}&success=true'.format(
                        self.lang, self.vocabs.get('name'), result))

        context = {
            u'vocab_name': self.vocab_name,
            u'vocab_name_name': self.template_mapper[self.vocab_name],
            u'tags': self.vocabs.get(u'tags', []),
            u'method': self.request.method,
            u'errors': self.errors,
            u'name': tag_name[0] if tag_name else '',
            u'created': success,
            u'localized_tags': all_labels,
            u'labels': self.format_labels(all_labels) if self.tag else self.format_list_labels(all_labels)
        }

        if self.tag:

            return base.render(u'admin/edit_create_vocab.html', extra_vars=context)
        return base.render(u'admin/list_vocabs.html', extra_vars=context)

    def add_tag(self, vocab, tag_name):
        data = {u'name': tag_name, u'vocabulary_id': vocab[u'id']}
        try:
            result = toolkit.get_action(u'tag_create')(self.context, data)
            self.localize_tags(result.get('id'))
            self.created = True
            return result.get('id')
        except ValidationError as e:
            if u'already belongs to vocabulary' in str(e):
                self.errors.append(_(u'Vocabulary tag is already existent.'))
                self.created = False
            return e
        return result

    def localize_tags(self, tag_id):
        labels = [
            {
                u'lang': lang,
                u'text': self.request.POST.get(lang, u''),
                u'name': self.vocabs[u'name'],
                u'id': tag_id,
            }
            for lang in self.available_locales
        ]
        TagMultilang.save_tags(*labels)

    def del_tag(self, context, vocab, tag_name):
        data = {u'id': tag_name, 'vocabulary_id': vocab[u'id']}
        return toolkit.get_action(u'tag_delete')(context, data)

    def get_package_name_validation_errors(self, package_name):
        context = {u'model': ckan.model, u'session': ckan.model.Session}
        schema = ckan.logic.schema.default_create_package_schema()

        data_dict = {u'name': package_name}
        data, errors = validate(data_dict, schema, context)
        return errors.get(u'name', [])

    def get_vocab(self, context, vocab_name):
        try:
            data = {u'id': vocab_name}
            return toolkit.get_action(u'vocabulary_show')(context, data)

        except toolkit.ObjectNotFound:
            return {}

    def url_errors(self):
        tags = [tag[u'id'] for tag in self.vocabs.get(u'tags', [])]
        return self.tag and (self.tag != u'NEW' and self.tag not in tags) \
            or not self.vocabs

    def format_labels(self, labels):
        label_dict = {}
        for label in labels:
            label_dict[label.lang] = label.text
        return label_dict

    def format_list_labels(self, labels):
        label_dict = {}
        for label in labels.filter(TagMultilang.lang == self.lang):
            label_dict[label.tag_id] = label.text
        return label_dict

