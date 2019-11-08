#encoding: utf-8

'''plugin.py

'''
import logging
import json
from collections import OrderedDict
from dateutil.parser import parse

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation

log = logging.getLogger(__name__)

FIELD_RESOURCE_TYPE = 'fao_resource_type'
FIELD_ACTIVITY_TYPE = 'fao_activity_type'
FIELD_FOCUS         = 'fao_geographic_focus'
FIELD_RELEASE_YEAR  = 'fao_release_year'
FIELD_RESOURCE_YEAR = 'fao_resource_release_year'

class FAOCLHGUIPlugin(plugins.SingletonPlugin,
                      toolkit.DefaultDatasetForm,
                      DefaultTranslation):

    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IPackageController)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITranslation)

    # IPackageController
    def before_search(self, search_params):
        return search_params

    def after_search(self, search_results, search_params):
        return search_results

    def before_index(self, dataset_dict):
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

    # IFacets
    def _fao_facets(self, src_facets_dict, package_type):
        facets_dict = OrderedDict()
        facets_dict[FIELD_RESOURCE_TYPE] = toolkit._('Type of Resource')
        facets_dict[FIELD_ACTIVITY_TYPE] = toolkit._('Kind of Activity')
        facets_dict[FIELD_FOCUS] = toolkit._('Geographic Focus')

        for k in ['tags', 'res_format', 'organization', 'groups']:
            facets_dict[k] = src_facets_dict[k]

        return facets_dict

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

    def _modify_package_schema(self, schema):
        # Our custom field

        schema.update({
            FIELD_RESOURCE_TYPE: [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_extras')],
        })

        schema.update({
            FIELD_ACTIVITY_TYPE: [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_extras')],
        })

        schema.update({
            FIELD_FOCUS: [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_extras')],
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
        # Our custom field

        schema.update({
            FIELD_RESOURCE_TYPE: [
                toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_missing')],
        })
        schema.update({
            FIELD_ACTIVITY_TYPE: [
                toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_missing')],
        })
        schema.update({
            FIELD_FOCUS: [
                toolkit.get_converter('convert_from_extras'),
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
