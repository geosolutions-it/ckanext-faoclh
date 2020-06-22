import csv
import json
import logging
import os
from datetime import datetime

import ckan.lib.base as base
import ckan.lib.jobs as jobs
import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
from ckan.controllers.admin import AdminController
from ckan.model import Package, PackageTag, Resource, Tag, Vocabulary, meta
from paste.fileapp import DataApp, FileApp
from ckan.common import config

log = logging.getLogger(__name__)


class ExportDatasetController(AdminController):
    def __init__(self):
        try:
            self.output_dir = config[u'faoclh.export_dataset_dir']
        except KeyError:
            raise Exception(u"Set a dataset export directory path in CKAN's configuration (production.ini)"
                            u" file using 'faoclh.export_dataset_dir' settings key")

        user = toolkit.get_action(u'get_site_user')({u'ignore_auth': True}, {})
        self.context = {u'user': user[u'name'], u'ignore_auth': True}
        self.request = base.request

    def export_dataset(self, *args, **kwargs):
        if self.request.method == u'POST':
            output_file = os.path.join(self.output_dir, u'{}.csv'.format(kwargs[u'pylons'].session.id))

            if os.path.exists(output_file):
                os.remove(output_file)

            result = jobs.enqueue(generate_dataset_csv, [
                                  self.output_dir, output_file, self.context])

            toolkit.response.headers[u'Content-Type'] = u'application/json'
            toolkit.response.status = u'201 CREATED'
            return json.dumps({u'generating_export': True})
        return base.render(u'admin/export_dataset.html')

    def download_dataset(self, *args, **kwargs):
        session_id = kwargs[u'pylons'].session.id
        toolkit.response.headers[u'Content-Type'] = u'application/json'
        output_filename = os.path.join(self.output_dir, u'{}.csv'.format(session_id))
        file_exists = os.path.exists(output_filename)

        if self.request.method == u'POST':
            if not file_exists:
                toolkit.response.status = u'204'
            return json.dumps({u'export_created': file_exists})

        return self._send_file_response(output_filename)

    def _send_file_response(self, output_filename):
        user_filename = u'_'.join(output_filename.split(u'/')[-2:])
        file_size = os.path.getsize(output_filename)

        headers = [(u'Content-Disposition', u'attachment; filename=\"dataset {}.csv\"'.format(
            datetime.now().strftime(u'%m-%d-%Y'))),
                   (u'Content-Type', u'text/plain'),
                   (u'Content-Length', str(file_size))]

        fapp = FileApp(output_filename, headers=headers)

        return fapp(self.request.environ, self.start_response)


class GetPackageData(Package):
    @classmethod
    def all_datasets(cls):
        return meta.Session.query(Package.id, Package.title, Package.metadata_created).all()

    @classmethod
    def get_all_tags(cls, package_id):
        package_tags = meta.Session.query(PackageTag.tag_id).filter(
            PackageTag.package_id == package_id)
        tags = meta.Session.query(Tag.name).filter(
            Tag.id.in_([tag[0] for tag in package_tags])).all()
        return u', '.join([tag[0] for tag in tags])

    @classmethod
    def get_resource(cls, model_field, package_id):
        resource = meta.Session.query(model_field).filter(
            Resource.package_id == package_id)
        field_mapper = {
            Resource.name: lambda package_resource: u', '.join([res[0] for res in package_resource]).encode(u'utf-8'),
            Resource.format: lambda package_resource: u', '.join(
                [res[0] for res in package_resource]).encode(u'utf-8')
        }
        return field_mapper[model_field](resource)

    @classmethod
    def get_resource_year_of_release(cls, years_of_release):
        try:
            return u', '.join(years_of_release)
        except TypeError:
            return u''


def generate_dataset_csv(output_dir, output_file, context):
    """
    Write tracking summary to a csv file.
    :return: None
    """
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    log.info(u'Creating dataset export file [path = {}]'.format(output_file))
    headings = [
        u'Dataset Title',
        u'Dataset Topics',
        u'Dataset Tags',
        u'Kind of Activity',
        u'Type of Resource',
        u'Resource Title',
        u'Resource Format',
        u'Year Of Release',
    ]

    datasets = GetPackageData.all_datasets()
    package_show = logic.get_action(u'package_show')

    with open(output_file, u'w') as fh:
        f_out = csv.writer(fh)
        f_out.writerow(headings)
        f_out.writerows([(
            dataset.title,
            (lambda topics: u', '.join([topic.get(u'name', u'') for topic in topics]))(
                package_show(context, {u'id': dataset.id})[u'groups']),
            GetPackageData.get_all_tags(package_id=dataset.id),
            (lambda act_type: act_type[0] if act_type else u'')(
                package_show(context, {u'id': dataset.id}).get(u'fao_activity_type')),
            (lambda res_type: res_type[0] if res_type else u'')(
                package_show(context, {u'id': dataset.id}).get(u'fao_resource_type')),
            GetPackageData.get_resource(Resource.name, dataset.id),
            GetPackageData.get_resource(Resource.format, dataset.id),
            GetPackageData.get_resource_year_of_release([
                item.get(u'custom_resource_text') for item in
                package_show(context, {u'id': dataset.id}).get(u'resources', {}) if item
            ])
        ) for dataset in datasets])

    log.info(u'Successfully created dataset export file [path = {}]'.format(output_dir))
