#encoding: utf-8

'''plugin.py

'''
import logging
import json
import os

from collections import OrderedDict

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
from ckan.common import config
import ckan.common as common
import ckan.logic as logic
from paste.deploy.converters import asbool
import ckan.model as model
from routes.mapper import SubMapper
from ckanext.multilang.model import TagMultilang
import ckanext.multilang.helpers as helpers
from ckan.model import Tag, meta
from sqlalchemy import or_

log = logging.getLogger(__name__)

FIELD_RESOURCE_TYPE = 'fao_resource_type'
FIELD_ACTIVITY_TYPE = 'fao_activity_type'
FIELD_FOCUS         = 'fao_geographic_focus'

FIELD_RELEASE_YEAR  = 'fao_release_year'
FIELD_RESOURCE_YEAR = 'fao_resource_release_year'

VOCAB_FIELDS = [FIELD_RESOURCE_TYPE, FIELD_ACTIVITY_TYPE, FIELD_FOCUS]

class FAOCLHGUIPlugin(plugins.SingletonPlugin,
                      toolkit.DefaultDatasetForm,
                      DefaultTranslation):

    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IPackageController)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes)

    # IPackageController
    def before_search(self, search_params):
        return search_params

    def after_search(self, search_results, search_params):
        return search_results

    def before_index(self, dataset_dict):
        # log.debug("BEFORE_INDEX")
        # log.debug("INDEXING {}".format(dataset_dict))

        for faokey in VOCAB_FIELDS:
            key = 'vocab_' + faokey
            v = dataset_dict.get(key, None)
            # log.debug("INDEXING {} -> ({}) {}".format(key, type(v), v))

            if v and isinstance(v, list):
                dataset_dict[faokey] = v[0]
                # log.debug("DUMPING {}".format(v[0]))

        return dataset_dict

    def before_view(self, pkg_dict):
        return pkg_dict

    def read(self, entity):
        return entity

    def create(self, entity):
        return entity

    def edit(self, entity):
        return entity

    def delete(self, entity):
        return entity

    def after_create(self, context, pkg_dict):
        return pkg_dict

    def after_update(self, context, pkg_dict):
        return pkg_dict

    def after_delete(self, context, pkg_dict):
        return pkg_dict

    def after_show(self, context, pkg_dict):
        return pkg_dict

    def setup_template_variables(self, context, data_dict):

        c = common.c
        translated_fields = {}

        if c.fields:
            for (key, val) in c.fields:
                if key in VOCAB_FIELDS:
                    label = fao_voc_label(key, val)
                    if label:
                        translated_fields[(key,val)] = label

        if translated_fields:
            c.translated_fields = translated_fields

    # IFacets
    def _fao_facets(self, src_facets_dict, package_type):
        facet_titles_order = [
            'groups', 'fao_activity_type', 'fao_resource_type', 'tags', 'fao_geographic_focus', 'organization',
            'res_format',
        ]

        def get_facet_value(field):
            try:
                return field, src_facets_dict[field]
            except KeyError:
                return field, toolkit._(field)

        return OrderedDict([get_facet_value(item) for item in facet_titles_order])

    def dataset_facets(self, facets_dict, package_type):
        return self._fao_facets(facets_dict, package_type)

    def organization_facets(self, facets_dict, organization_type, package_type):
        return self._fao_facets(facets_dict, package_type)

    def group_facets(self, facets_dict, group_type, package_type):
        return self._fao_facets(facets_dict, package_type)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', "faoclh")

    def before_map(self, map_obj):
        u'''
        Called before the routes map is generated. ``before_map`` is before any
        other mappings are created so can override all other mappings.

        :param map: Routes map object
        :returns: Modified version of the map object
        '''
        with SubMapper(map_obj, controller=u'ckanext.faoclh.controllers.admin:AdminController') as mp:
            mp.connect(u'list_vocab_tags', u'/ckan-admin/vocabulary/all/{vocabulary_name:.*}',
                       action=u'list_vocabulary_view')
            mp.connect(u'edit_vocabs_tags', u'/ckan-admin/vocabulary/edit/{vocabulary_name:.*}/tag/{tag_id:.*}',
                       action=u'update_vocabulary_tag_view')
            mp.connect(u'create_vocabs_tags', u'/ckan-admin/vocabulary/create/{vocabulary_name:.*}',
                       action=u'create_vocabulary_tag_view')
            mp.connect(u'delete_vocabs_tags', u'/ckan-admin/vocabulary/delete/{vocabulary_name:.*}/tag/{tag_id:.*}',
                       action=u'delete_vocabulary_tag_view')
        return map_obj

    def after_map(self, map_obj):
        u'''
        Called after routes map is set up. ``after_map`` can be used to
        add fall-back handlers.

        :param map: Routes map object
        :returns: Modified version of the map object
        '''
        return map_obj

    def _modify_package_schema(self, schema):
        # Our custom field

        for field in VOCAB_FIELDS:
            schema.update({
                field: [
                    toolkit.get_validator('ignore_missing'),
                    toolkit.get_converter('convert_to_tags')(field)],
            })

        schema.update({
            FIELD_RELEASE_YEAR: [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_extras')],
        })

        # Add our custom_RESOURCE_text metadata field to the schema
        schema['resources'].update({
            FIELD_RESOURCE_YEAR: [toolkit.get_validator('ignore_missing')]
        })

        return schema

    def create_package_schema(self):
        # Get default schema
        schema = super(FAOCLHGUIPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        # Get default schema
        schema = super(FAOCLHGUIPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        # Get default schema
        schema = super(FAOCLHGUIPlugin, self).show_package_schema()

        # we're using tags as internal fields, so don't include vocab tags in the free tags
        schema['tags']['__extras'].append(toolkit.get_converter('free_tags_only'))

        # Our custom field
        for field in VOCAB_FIELDS:
            schema.update({
                field: [
                    toolkit.get_converter('convert_from_tags')(field),
                    toolkit.get_validator('ignore_missing')],
            })

        schema.update({
            FIELD_RELEASE_YEAR: [
                toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_missing')],
        })

        schema['resources'].update({
            FIELD_RESOURCE_YEAR: [
                toolkit.get_validator('ignore_missing')]
        })

        return schema

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'fao_voc': fao_voc,
            'fao_voc_label': fao_voc_label,
            'fao_voc_label_func': fao_voc_label_func,
            'fao_get_search_facet': fao_get_search_facet
        }


def fao_voc(voc_name):
    try:
        data = {u'id': voc_name}
        tags = toolkit.get_action(u'vocabulary_show')({}, data).get(u'tags', [])
        tag_dict = {tag.get(u'id'):tag.get(u'display_name') for tag in tags}

    except toolkit.ObjectNotFound:
        tag_dict = {}

    lang = helpers.getLanguage()
    all_labels = TagMultilang.get_all(voc_name, lang)

    def get_tag_label(tag_id):
        tag = all_labels.filter(TagMultilang.tag_id == tag_id, TagMultilang.lang == lang).first()
        if tag:
            return tag.text

    return [{
                u'name': value,
                u'label': get_tag_label(tag_id) or value
            } for tag_id, value in tag_dict.iteritems()]


def fao_voc_label(voc_name, tag_name):
    if not tag_name:
        log.warn(u'Empty tag for vocab "{}"'.format(voc_name))
        return None
    if isinstance(tag_name, list):
        tag_name = tag_name[0]

    tag_id = meta.Session.query(Tag.id).filter(Tag.name == tag_name).first()

    if tag_id:
        multilang_tag = meta.Session.query(TagMultilang.text).filter(
            TagMultilang.tag_name == voc_name, TagMultilang.tag_id == tag_id,
            TagMultilang.lang == helpers.getLanguage()
        ).first()
    else:
        multilang_tag = meta.Session.query(TagMultilang.text).filter(
            TagMultilang.tag_name == u'{}:{}'.format(voc_name, tag_name),
            TagMultilang.lang == helpers.getLanguage()
        ).first()

    return multilang_tag[0] if multilang_tag else tag_name


def fao_voc_label_func(voc_name):
    return lambda item: fao_voc_label(voc_name, item.get('name'))

def fao_get_search_facet(limit=6):

    context = {
        'model': model,
        'session': model.Session,
        'user': common.c.user,
        'for_view': True,
        'auth_user_obj': common.c.userobj
    }

    data_dict = {
        'q': '*:*',
        'fq': '',
        'facet.field': VOCAB_FIELDS,
        'rows': limit,
        'start': 0,
        'sort': 'count desc',
        'extras': {},
        'include_private': asbool(config.get(
            'ckan.search.default_include_private', True)
        ),
    }

    query = logic.get_action('package_search')(context, data_dict)

    fao_search_facets = query['search_facets']

    result = {}

    for field in VOCAB_FIELDS:
        try:
            items = fao_search_facets[field]['items']
            items.sort(key=lambda item: item['count'], reverse=True)
            result[field] = items[:limit]
        except KeyError:
            result[field] = []

    return result
