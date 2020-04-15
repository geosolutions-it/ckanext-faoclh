import ckan.lib.base as base
import logging
from ckanext.faoclh.cli.vocab import VocabCommand

log = logging.getLogger(__name__)

class VocabularyController(base.BaseController):
    def vocabularies(self, *args, **kwargs):
        template_mapper = {
            'fao_resource_type': 'Resource Type',
            'fao_activity_type': 'Activity Type',
            'fao_geographic_focus': 'Geographical Focus'
        }

        vocab_type = kwargs['pylons'].request.GET.get('vocab_type', 'fao_resource_type')
        pk = kwargs['pylons'].request.GET.get('id', None)
        # action = kwargs['pylons'].request.GET.get('action', None)

        vocab_obj = VocabCommand._tags_get({}, pk)
        tags = VocabCommand._vocab_get({}, vocab_type).get('tags', [])
        log.info('log ->> {}'.format(vocab_obj))

        context = {
            'vocab_type': vocab_type,
            'vocab_type_name': template_mapper[vocab_type],
            'tags': tags,
            'method': kwargs['pylons'].request.method
        }

        if pk:
            return base.render('admin/edit_create_vocab.html', extra_vars=context)
        return base.render('admin/list_vocabs.html', extra_vars=context)
