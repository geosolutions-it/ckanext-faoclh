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
        # action = kwargs['pylons'].request.GET.get('action', None)

        vocab_obj = VocabCommand._tags_get({}, vocab_type)
        tags = VocabCommand._vocab_get({}, vocab_type).get('tags', [])
        log.info('log ->> {}'.format(vocab_obj))

        context = {
            'vocal_type': vocab_type,
            'vocab_obj': vocab_obj,
            'tags': tags,
            'method': kwargs['pylons'].request.method
        }
        return base.render('admin/vocabs.html', extra_vars=context)
