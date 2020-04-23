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
from ckanext.multilang.model import PackageMultilang, TagMultilang
from ckan.model import Tag
from ckanext.multilang.model import PackageMultilang, GroupMultilang, TagMultilang

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
        request = kwargs[u'pylons'].request
        name = request.POST.get(u'name', u'')

        lang = helpers.getLanguage()

        self.vocab_name = request.GET.get(u'vocab_name', u'fao_resource_type')
        self.tag_name = request.GET.get(u'tag_name', u'')
        self.vocabs = self.get_vocab({}, self.vocab_name)

        all_labels = TagMultilang.all_by_name(self.vocabs['id'])
        print('all_labels', all_labels)

        if self.url_errors():
            return base.abort(404)

        if request.method == u'POST':
            all_vocab_tags = Tag.all(self.vocabs['id'])
            get_tag = (lambda tag: tag.name == self.tag_name)
            tag = filter(get_tag, all_vocab_tags)
            self.errors = self.get_package_name_validation_errors(name)
            labels = []
            if tag:
                labels = [
                    {
                        u'lang': lang,
                        u'text': request.POST.get(lang, u''),
                        u'name': self.vocabs[u'id'],
                        u'id': tag[0].id,
                    }
                    for lang in self.available_locales
                ]

            if not self.errors:
                print('labels', labels)
                TagMultilang.save_tags(*labels)
                if self.tag_name != u'NEW':
                    self.del_tag(self.context, self.vocabs, self.tag_name)

                self.add_tag(self.context, self.vocabs, name)

        context = {
            u'vocab_name': self.vocab_name,
            u'vocab_name_name': self.template_mapper[self.vocab_name],
            u'tags': self.vocabs.get(u'tags', []),
            u'method': request.method,
            u'errors': self.errors,
            u'name': self.tag_name if self.tag_name != u'NEW' else name,
            u'created': self.created,
            u'available_locales': self.available_locales,
        }

        if self.tag_name:

            return base.render(u'admin/edit_create_vocab.html', extra_vars=context)
        return base.render(u'admin/list_vocabs.html', extra_vars=context)

    def add_tag(self, context, vocab, tag_name):
        vocab_name = vocab[u'name']
        data = {u'name': tag_name, u'vocabulary_id': vocab[u'id']}
        try:
            result = toolkit.get_action(u'tag_create')(self.context, data)
            self.created = True
        except ValidationError as e:
            if u'already belongs to vocabulary' in str(e):
                self.errors.append(_(u'Vocabulary tag is already existent.'))
                self.created = False
            return e
        return result

    def del_tag(self, context, vocab, tag_name):
        vocab_name = vocab[u'name']
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
        tags = [tag[u'name'] for tag in self.vocabs.get(u'tags', [])]
        return self.tag_name and (self.tag_name != u'NEW' and self.tag_name not in tags) \
            or not self.vocabs

    # def persist_tags(self, tags):
    #     TagMultilang.persist({'id': tag_id, 'name': tag.get('key'), 'text': tag.get('value')}, lang)
