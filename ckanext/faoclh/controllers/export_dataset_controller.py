import csv
import json
import logging
import os
from datetime import datetime

from ckan.common import session
import ckan.lib.base as base
import ckan.lib.jobs as jobs
from ckan.lib.redis import connect_to_redis
import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
from ckan.controllers.admin import AdminController
from ckan.model import Package, PackageTag, Resource, Tag, Vocabulary, meta
from paste.fileapp import DataApp, FileApp
from ckan.common import config
from sqlalchemy import or_
from rq.job import Job

from ckanext.faoclh.plugin import FAO_TAG_FIELDS

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

            task = jobs.enqueue(generate_dataset_csv, [
                                  self.output_dir, output_file, self.context])

            toolkit.response.headers[u'Content-Type'] = u'application/json'
            toolkit.response.status = u'201 CREATED'
            session[u'background_task_id'] = task.id
            session.save()

            return json.dumps({u'generating_export': True})
        return base.render(u'admin/export_dataset.html')

    def download_dataset(self, *args, **kwargs):
        session_id = kwargs[u'pylons'].session.id
        toolkit.response.headers[u'Content-Type'] = u'application/json'
        output_filename = os.path.join(self.output_dir, u'{}.csv'.format(session_id))
        file_exists = Job.fetch(session[u'background_task_id'], connection=connect_to_redis())\
                          .get_status() == u'finished'

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


def generate_dataset_csv(output_dir, output_file, context):
    """
    Write dataset summary to a csv file.
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
        u'Resource Title',
        u'Type of Resource',
        u'Resource Format',
        u'Year Of Release',
    ]

    datasets = GetPackageData.all_datasets()
    package_show = logic.get_action(u'package_show')

    with open(output_file, u'w') as fh:
        f_out = csv.writer(fh)
        f_out.writerow(headings)
        for dataset in datasets:
            pkg = package_show(context, {u'id': dataset.id})
            resources = pkg.get(u'resources', {})
            row = (
                dataset.title,
                ', '.join([topic.get(u'name', u'') for topic in pkg['groups']]),
                ', '.join([tag['name'] for tag in pkg.get('tags', []) if tag['vocabulary_id'] is None]),
                ', '.join(pkg.get(u'fao_activity_type', ['No activity type'])),  # 0 or 1
                ', '.join([res.get('name', 'Unnamed resource') for res in resources]),
                ', '.join([res.get('fao_resource_type', '-') for res in resources]),
                ', '.join([res.get('format', '-') for res in resources]),
                ', '.join([res.get('custom_resource_text',  '-') for res in resources])
            )
            f_out.writerow(row)

    log.info(u'Successfully created dataset export file [path = {}]'.format(output_dir))
