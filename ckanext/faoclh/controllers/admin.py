import logging

import ckan.lib.base as base
import ckan.plugins.toolkit as toolkit
import ckanext.multilang.helpers as helpers
from ckan.common import _
from ckan.controllers.admin import AdminController
from ckan.lib.i18n import get_locales_from_config
from ckan.logic import ValidationError
from ckan.model import Tag, meta
from ckanext.multilang.model import TagMultilang

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
        status = self.request.GET.get('status')

        return self.prepare_response(u'admin/list_vocabs.html', **{
            u'vocab_name': vocab_name,
            u'tags': vocabulary.get(u'tags', []),
            u'labels': self.format_list_labels(localized_tags, helpers.getLanguage()),
            u'status': status,
        })

    def delete_vocabulary_tag_view(self, *args, **kwargs):
        vocab_name = kwargs.get(u'vocabulary_name', u'fao_resource_type')
        vocabulary = self.get_vocab({}, vocab_name)
        tag_id = kwargs.get(u'tag_id', None)

        try:
            self.del_tag(self.context, vocabulary, tag_id)
            toolkit.redirect_to(u'/ckan-admin/vocabulary/all/{}?status=deleted'.format(
                vocab_name))
        except toolkit.ObjectNotFound:
            return base.abort(404)

    def create_vocabulary_tag_view(self, *args, **kwargs):
        return self.http_method_handler(self.request, *args, **kwargs)

    def update_vocabulary_tag_view(self, *args, **kwargs):
        return self.http_method_handler(self.request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        tag_name = request.POST.get(u'tag_name', u'')
        vocab_name = kwargs.get(u'vocabulary_name', u'fao_resource_type')
        tag_id = kwargs.get(u'tag_id', None)
        vocabulary = self.get_vocab({}, vocab_name)

        if tag_id:
            self.update_tag(tag_id, tag_name, vocab_name)
            status = 'edited'
        else:
            status = 'created'
            result = self.add_tag(vocabulary, tag_name, vocab_name)

        if self.created:
            toolkit.redirect_to(u'/ckan-admin/vocabulary/edit/{}/tag/{}?status={}'.format(
                vocab_name, tag_id or result, status))

        return self.prepare_response(u'admin/edit_create_vocab.html', **{
            u'vocab_name': vocab_name,
            u'errors': self.errors,
            u'labels': {lang: self.request.POST.get(lang, u'').strip()
                        for lang in self.available_locales},
            u'tag_name': tag_name,
            u'tag_id': tag_id,
        })

    def get(self, request, *args, **kwargs):
        vocab_name = kwargs.get(u'vocabulary_name', u'fao_resource_type')
        tag_id = kwargs.get(u'tag_id', None)
        vocabulary = self.get_vocab({}, vocab_name)
        localized_tags = TagMultilang.get_all(vocab_name)
        status = self.request.GET.get('status')

        if tag_id:
            localized_tags = localized_tags.filter(
                TagMultilang.tag_id == tag_id)
            if not Tag.by_id(tag_id):
                return base.abort(404)

        tag_name = [tag[u'display_name']
                    for tag in vocabulary.get(u'tags', []) if tag[u'id'] == tag_id]

        return self.prepare_response(u'admin/edit_create_vocab.html', **{
            u'vocab_name': vocab_name,
            u'labels': self.format_labels(localized_tags),
            u'tag_name': tag_name[0] if tag_name else '',
            u'tag_id': tag_id,
            u'status': status,
        })

    def prepare_response(self, template, **kwargs):
        try:
            vocab_label = self.vocab_name_template_mapper[kwargs.get(
                u'vocab_name')]
        except KeyError:
            return base.abort(404)
        kwargs[u'vocab_label'] = vocab_label
        kwargs[u'active'] = True

        return base.render(template, extra_vars=kwargs)

    def update_tag(self, tag_id, tag_name, vocab_name):
        tag = meta.Session.query(Tag).get(tag_id)
        tag.name = tag_name
        meta.Session.commit()
        self.localize_tags(tag.id, vocab_name)
        self.created = True

    def add_tag(self, vocab, tag_name, vocab_name):
        data = {u'name': tag_name.strip(), u'vocabulary_id': vocab[u'id']}
        try:
            result = toolkit.get_action(u'tag_create')(self.context, data)
            self.localize_tags(result.get(u'id'), vocab_name)
            self.created = True
            return result.get(u'id')
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
                u'text': self.request.POST.get(lang, u'').strip(),
                u'name': vocab_name,
                u'id': tag_id,
            }
            for lang in self.available_locales
        ]
        TagMultilang.save_tags(*labels)

    @staticmethod
    def del_tag(context, vocab, tag_name):
        data = {u'id': tag_name, u'vocabulary_id': vocab[u'id']}
        return toolkit.get_action(u'tag_delete')(context, data)

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
