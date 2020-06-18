import logging
import os

import ckan.lib.base as base
import ckan.plugins.toolkit as toolkit
import ckanext.multilang.helpers as helpers
from ckan.common import _
from ckan.controllers.admin import AdminController
from ckan.lib.i18n import get_locales_from_config
from ckan.logic import ValidationError
from ckan.model import Tag, meta
from ckanext.multilang.model import TagMultilang
from ckanext.faoclh.model.tag_image_url import TagImageUrl
from ckan.lib.uploader import get_storage_path
from sqlalchemy import exc
import shutil

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
            u'GET': self.get,
            u'POST': self.post,
        }

        self.errors = []
        self.available_locales = get_locales_from_config()
        user = toolkit.get_action(u'get_site_user')({u'ignore_auth': True}, {})
        self.context = {u'user': user[u'name'], u'ignore_auth': True}
        self.request = base.request
        self.http_method_handler = self.method_mapper[self.request.method]

    def list_vocabulary_view(self, *args, **kwargs):
        vocab_name = kwargs.get(u'vocabulary_name', u'fao_resource_type')
        vocabulary = self.get_vocab({}, vocab_name)
        localized_tags = TagMultilang.get_all(vocab_name)
        status = self.request.GET.get(u'status')

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
        image_upload = request.POST.get(u'image_upload')
        image_url = request.POST.get(u'image_url')
        tag_id = kwargs.get(u'tag_id')
        vocabulary = self.get_vocab({}, vocab_name)

        if tag_id:
            self.update_tag(tag_id, tag_name, vocab_name, image_upload, image_url)
            status = u'edited'
        else:
            status = u'created'
            result = self.add_tag(vocabulary, tag_name, vocab_name, image_upload, image_url)

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
        status = self.request.GET.get(u'status')

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
            u'tag_name': tag_name[0] if tag_name else u'',
            u'tag_id': tag_id,
            u'status': status,
            u'image_url': TagImageUrl.get_tag_image_url(tag_id) or u''
        })

    def create_or_update_tag_image_url(self, **tag_image_dict):
        try:
            TagImageUrl.persist(**tag_image_dict)
        except exc.IntegrityError:
            TagImageUrl.update(**tag_image_dict)

    def prepare_response(self, template, **kwargs):
        try:
            vocab_label = self.vocab_name_template_mapper[kwargs.get(
                u'vocab_name')]
        except KeyError:
            return base.abort(404)
        kwargs[u'vocab_label'] = vocab_label
        kwargs[u'active'] = True

        return base.render(template, extra_vars=kwargs)

    def get_tag_image_url(self, image_upload, image_url, tag_id):
        try:
            file_ext = image_upload.filename.split(u'.')[-1]
        except AttributeError:
            return image_url
        if file_ext.lower() in [u'jpg', u'gif', u'png', u'webp', u'jpeg', u'svg']:
            path = get_storage_path()
            if not path:
                raise Exception(u'Image storage directory not configured. Use the "ckan.storage_path" settings key to '
                                u'specify image storage directory')
            storage_path = os.path.join(path, u'storage', u'tag_images')
            try:
                os.makedirs(storage_path)
            except OSError as e:
                log.debug(u'Debug: {}'.format(e))
            file_path = u'{}.{}'.format(tag_id, file_ext)

            output_file_path = os.path.join(storage_path, file_path)
            with open(output_file_path, u'wb') as output_file:
                shutil.copyfileobj(image_upload.file, output_file)
            return os.path.join(u'/tag_images', file_path)

    def update_tag(self, tag_id, tag_name, vocab_name, image_upload, image_url):
        tag = meta.Session.query(Tag).get(tag_id)
        if tag.name != tag_name.strip():
            new_tag_name = u'{}:{}'.format(vocab_name, tag.name)
            query = meta.Session.query(TagMultilang).filter(TagMultilang.tag_name == new_tag_name)
            if not query.count():
                self.localize_tags(tag_id, new_tag_name)

        tag.name = tag_name.strip()
        meta.Session.commit()
        self.update_localized_tags(tag.id, vocab_name)
        self.create_or_update_tag_image_url(**{
            u'tag_id': tag.id,
            u'image_url': self.get_tag_image_url(image_upload, image_url, tag_id),
            u'vocabulary': vocab_name,
            u'tag_name': tag_name
        })
        self.created = True

    def add_tag(self, vocab, tag_name, vocab_name, image_upload, image_url):
        data = {u'name': tag_name.strip(), u'vocabulary_id': vocab[u'id']}
        try:
            result = toolkit.get_action(u'tag_create')(self.context, data)
            self.localize_tags(result.get(u'id'), vocab_name)
            self.create_or_update_tag_image_url(**{
                u'tag_id': result.get(u'id'),
                u'image_url': self.get_tag_image_url(image_upload, image_url, result.get(u'id')),
                u'vocabulary': vocab_name,
                u'tag_name': tag_name
            })
            self.created = True
            return result.get(u'id')
        except ValidationError as e:
            if u'already belongs to vocabulary' in str(e):
                self.errors.append(_(u'Vocabulary tag is already existent.'))
                self.created = False
            return e
        return result

    def update_localized_tags(self, tag_id, vocab_name):
        multilang_tags = meta.Session.query(TagMultilang).filter(TagMultilang.tag_id == tag_id)

        if multilang_tags.count():
            tag_mapping = [{
                u'id': multilang_tag.id,
                u'text': self.request.POST.get(multilang_tag.lang, u'').strip()
            } for multilang_tag in multilang_tags]
            meta.Session.bulk_update_mappings(TagMultilang, tag_mapping)
            meta.Session.commit()
        else:
            self.localize_tags(tag_id, vocab_name)

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
        return {label.lang: label.text for label in labels}

    @staticmethod
    def format_list_labels(labels, lang):
        label_dict = {}
        for label in labels.filter(TagMultilang.lang == lang):
            label_dict[label.tag_id] = label.text
        return label_dict
