import logging

import ckan
import ckan.lib.base as base
import ckan.plugins.toolkit as toolkit
from ckan.common import _
from ckan.lib.navl.dictization_functions import validate
from ckan.logic import NotFound, ValidationError
from ckanext.faoclh.cli.vocab import VocabCommand

log = logging.getLogger(__name__)


class VocabularyController(base.BaseController):
    def vocabularies(self, *args, **kwargs):
        self.errors = []
        self.template_mapper = {
            u'fao_resource_type': u'Resource Type',
            u'fao_activity_type': u'Activity Type',
            u'fao_geographic_focus': u'Geographical Focus'
        }
        request = kwargs[u'pylons'].request
        name = request.POST.get(u'name', u'')
        label = request.POST.get(u'label', u'')

        self.vocab_name = request.GET.get(u'vocab_name', u'fao_resource_type')
        self.tag_name = request.GET.get(u'tag_name', u'')

        self.vocabs = self.get_vocab({}, self.vocab_name)

        if self.url_errors():
            return base.abort(404)

        if request.method == u'POST':
            self.errors = self.get_package_name_validation_errors(name)
            log.info('validation err ->> {}: {} '.format(name, self.errors))
            if not self.errors:
                if self.tag_name != 'NEW':
                    self.del_tag({}, self.vocabs, self.tag_name)

                self.add_tag({}, self.vocabs, name)

        log.info('tages ->> {}'.format(self.vocabs))
        context = {
            u'vocab_name': self.vocab_name,
            u'vocab_name_name': self.template_mapper[self.vocab_name],
            u'tags': self.vocabs.get('tags', []),
            u'method': request.method,
            u'errors': self.errors,
            u'name': self.tag_name if self.tag_name != 'NEW' else name,
        }

        if self.tag_name:
            return base.render(u'admin/edit_create_vocab.html', extra_vars=context)
        return base.render(u'admin/list_vocabs.html', extra_vars=context)

    def add_tag(self, context, vocab, tag_name):
        vocab_name = vocab['name']
        data = {'name': tag_name, 'vocabulary_id': vocab['id']}
        try:
            result = toolkit.get_action('tag_create')(context, data)
            log.info('success ->> {}'.format(result))
        except ValidationError as e:
            if u'already belongs to vocabulary' in str(e):
                self.errors.append(_(u'Vocabulary tag is already existent.'))
            return e
        return result

    def del_tag(self, context, vocab, tag_name):
        vocab_name = vocab['name']
        data = {'id': tag_name, 'vocabulary_id': vocab['id']}
        return toolkit.get_action('tag_delete')(context, data)

    def get_package_name_validation_errors(self, package_name):
        context = {u'model': ckan.model, u'session': ckan.model.Session}
        schema = ckan.logic.schema.default_create_package_schema()

        data_dict = {u'name': package_name}
        data, errors = validate(data_dict, schema, context)
        return errors.get(u'name', [])

    def get_vocab(self, context, vocab_name):
        try:
            data = {'id': vocab_name}
            return toolkit.get_action('vocabulary_show')(context, data)

        except toolkit.ObjectNotFound:
            return {}

    def url_errors(self):
        tags = [tag['name'] for tag in self.vocabs.get('tags', [])]
        return self.tag_name and (self.tag_name != 'NEW' and self.tag_name not in tags) \
            or not self.vocabs
