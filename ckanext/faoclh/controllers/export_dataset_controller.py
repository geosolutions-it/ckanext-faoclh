import ckan.lib.base as base
import csv
import os
from ckan.controllers.admin import AdminController
from paste.fileapp import FileApp, DataApp
import ckan.lib.jobs as jobs
import logging
import json
from datetime import datetime


log = logging.getLogger(__name__)


class ExportDatasetController(AdminController):
    def __init__(self):
        self.output_dir = u'/usr/lib/ckan/src/ckanext-faoclh/ckanext_faoclh.egg-info/exported-dataset/'

    def export_dataset(self, *args, **kwargs):
        request = kwargs[u'pylons'].request
        print('heheh', kwargs[u'pylons'].response.status)
        if request.method == u'POST':
            result = jobs.enqueue(generate_dataset_csv, [self.output_dir, kwargs[u'pylons'].session.id])
            print('heheh', result)
            kwargs[u'pylons'].response.headers['Content-Type'] = 'application/json'
            kwargs[u'pylons'].response.status = '201 CREATED'
            return json.dumps({u'generating_export': True})
        return base.render(u'admin/export_dataset.html')

    def download_dataset(self, *args, **kwargs):
        self.request = kwargs[u'pylons'].request
        session_id = kwargs[u'pylons'].session.id
        kwargs[u'pylons'].response.headers['Content-Type'] = 'application/json'
        output_filename = self.output_dir + u'{}.csv'.format(session_id)
        file_exists = os.path.exists(output_filename)

        if self.request.method == u'POST':
            if not file_exists:
                kwargs[u'pylons'].response.status = '204'
            return json.dumps({u'export_created': file_exists})

        return self._send_file_response(output_filename)

    # def _check_file_existance(self, output_filename):
    #     headers = [(u'Content-Type', u'application/json')]

        # if not os.path.exists(output_filename):
            # dapp = DataApp(json.dumps({u'export_generated': False}), headers=headers)
            # return dapp(self.request.environ, self.start_response)
            # return json.dumps({u'export_generated': True})
        # return self._send_file_response(output_filename)

    def _send_file_response(self, output_filename):
        user_filename = '_'.join(output_filename.split(u'/')[-2:])
        file_size = os.path.getsize(output_filename)

        headers = [(u'Content-Disposition', u'attachment; filename=\"' + user_filename + u'\"'),
                   (u'Content-Type', u'text/plain'),
                   (u'Content-Length', str(file_size))]

        fapp = FileApp(output_filename, headers=headers)

        return fapp(self.request.environ, self.start_response)


def generate_dataset_csv(output_dir, session_id):
    """
    Write tracking summary to a csv file.
    :return: None
    """
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    output_file = output_dir + u'{}.csv'.format(session_id)
    log.info(u'Creating dataset export file [path = {}]'.format(output_file))
    headings = [
        u'Dataset Title',
        u'Dataset Topics',
        u'Dataset Tags',
        u'Kind of Activity',
        u'Type of Resource',
        u'Resource Title',
        u'Resource Format',
        u'Year Of Release'
    ]
    with open(output_file, 'w') as fh:
        f_out = csv.writer(fh)
        f_out.writerow(headings)
        f_out.writerows([('hehhe', 'jd', 'kjdh', 'kjdh', 'nhd', 'kjdhf', 'jdh', r)
                        for r in range(10)])

    log.info(u'Successfully created dataset export file [path = {}]'.format(session_id, output_dir))
