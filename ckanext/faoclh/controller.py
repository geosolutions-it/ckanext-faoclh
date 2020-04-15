import logging

import ckan
import ckan.lib.base as base
import ckan.plugins.toolkit as toolkit
from ckan.lib.navl.dictization_functions import validate
from ckan.logic import ValidationError
from ckanext.faoclh.cli.vocab import VocabCommand

log = logging.getLogger(__name__)


class VocabularyController(base.BaseController):
    def vocabularies(self, *args, **kwargs):
        self.errors = []
        template_mapper = {
            u'fao_resource_type': u'Resource Type',
            u'fao_activity_type': u'Activity Type',
            u'fao_geographic_focus': u'Geographical Focus'
        }
        request = kwargs[u'pylons'].request
        name = request.POST.get(u'name', u'')
        label = request.POST.get(u'label', u'')

        vocab_name = request.GET.get(u'vocab_name', u'fao_resource_type')
        pk = request.GET.get(u'id', None)

        vocabs = VocabCommand._vocab_get({}, vocab_name)
        log.info('log ->> {}'.format(vocabs))

        if request.method == u'POST':
            self.errors = self.get_package_name_validation_errors(name)
            log.info('validation err ->> {}: {} '.format(name, self.errors))
            if not self.errors:
                self.add_tag({}, vocabs, name)

        context = {
            u'vocab_name': vocab_name,
            u'vocab_name_name': template_mapper[vocab_name],
            u'tags': vocabs.get('tags', []),
            u'method': request.method,
            u'errors': self.errors,
            u'name': name,
        }

        if pk:
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
                self.errors.append(u'Vocabulary tag is already existent.')
            return e
        return result

    def get_package_name_validation_errors(self, package_name):
        context = {u'model': ckan.model, u'session': ckan.model.Session}
        schema = ckan.logic.schema.default_create_package_schema()

        data_dict = {u'name': package_name}
        data, errors = validate(data_dict, schema, context)
        return errors.get(u'name', [])
