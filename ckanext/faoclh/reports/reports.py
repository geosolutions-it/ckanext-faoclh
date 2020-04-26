from __future__ import division

import logging
from datetime import datetime

from sqlalchemy import and_, func, or_

import ckan.plugins.toolkit as t
from ckan import model
from ckan.common import OrderedDict
from ckanext.faoclh.checkers import check_url

try:
    from babel.support import NullTranslation
    from flask.ext.babel import lazy_gettext as _
except ImportError:
    from pylons.i18n import lazy_ugettext as _
log = logging.getLogger(__name__)

DEFAULT_CTX = {'ignore_auth': True}
DEFAULT_ORG_CTX = DEFAULT_CTX.copy()
BROKEN_LINKS_MARKER = None
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
broken_links_options = OrderedDict({'org': None})
tagless_datasets_options = OrderedDict({'org': None})
unpublished_dataset_options = OrderedDict({'org': None})
dataset_without_resources_options = OrderedDict({'org': None})


def dformat(val):
    """
    Return timestamp as string
    """
    if isinstance(val, datetime):
        return val.strftime(DATE_FORMAT)


def row_dict_norm(val_in):
    return dict(_dict_to_row(val_in))


def broken_links_options_combinations():
    organizations = _get_organizations()
    return [{'org': org} for org in organizations]


def _dict_to_row(val_in):
    """
    Translates nested dictionaries into
      key1.subkey2, value

      list
    """
    out = []

    # keep order
    keys = sorted(val_in.keys())
    for k in keys:
        v = val_in[k]
        if not isinstance(v, dict):
            out.append((k, v,))
        else:
            sub_out = _dict_to_row(v)
            for item in sub_out:
                out.append(('{}.{}'.format(k, item[0]),
                            item[1],))
    return out


def _get_organizations():
    call = t.get_action('organization_list')
    orgs = call(DEFAULT_ORG_CTX, {})
    return orgs + [None]


def report_broken_links(org=None, dataset=None):
    """
    """
    # used in get_report_data to detect if report was
    # created within the same session
    global BROKEN_LINKS_MARKER
    if BROKEN_LINKS_MARKER is None:
        BROKEN_LINKS_MARKER = dformat(datetime.now())

    from ckanext.report.report_registry import ReportRegistry, extract_entity_name
    from ckanext.report.model import DataCache

    def get_report_data(options_dict):
        reg = ReportRegistry.instance()
        rep = reg.get_report('broken-links')

        entity_name = extract_entity_name(options_dict)
        key = rep.generate_key(options_dict)
        data, date = DataCache.get(entity_name, key, convert_json=True)
        if data['marker'] == BROKEN_LINKS_MARKER if data else False:
            return data

    def get_report_summary(data):

        out = {'total.resources': 0,
               'total.datasets': 0,
               'errors.resources': 0,
               'errors.datasets': 0,
               'errors.resources_pct': 0,
               'errors.datasets_pct': 0
               }

        for row in data:
            out['total.resources'] += row['total.resources']
            out['total.datasets'] += row['total.datasets']
            out['errors.resources'] += row['errors.resources']
            out['errors.datasets'] += row['errors.datasets']

        if out['total.resources'] > 0:
            out['errors.resources_pct'] = out['errors.resources'] * \
                100.0 / out['total.resources']
        else:
            out['errors.resources_pct'] = 0.0
        if out['total.datasets'] > 0:
            out['errors.datasets_pct'] = out['errors.datasets'] * \
                100.0 / out['total.datasets']
        else:
            out['errors.datasets_pct'] = 0.0
        return out

    def get_report_stats(data, org_name):
        out = {'organization': org_name}
        out.update(dict(((k, v,)
                         for k, v in data.items() if k.startswith('total.'))))
        out.update(dict(((k, v,)
                         for k, v in data.items() if k.startswith('errors.'))))

        if data['total.resources'] > 0:
            out['errors.resources_pct'] = data['errors.resources'] * \
                100.0 / data['total.resources']
        else:
            out['errors.resources_pct'] = 0.0
        if data['total.datasets'] > 0:
            out['errors.datasets_pct'] = data['errors.datasets'] * \
                100.0 / data['total.datasets']
        else:
            out['errors.datasets_pct'] = 0.0
        return out

    s = model.Session
    R = model.Resource
    D = model.Package
    O = model.Group

    if org or dataset:
        q = s.query(R) \
            .join(D, D.id == R.package_id) \
            .filter(and_(R.state == 'active',
                         D.state == 'active')) \
            .order_by(R.url)
        if org:
            q = q.join(O, O.id == D.owner_org).filter(O.name == org)
        if dataset:
            q = q.filter(or_(D.name == dataset,
                             D.id == dataset,
                             D.title == dataset))
        table = []
        count = q.count()
        log.info("Checking broken links for %s items", count)

        # we need dataset count later, in summary report
        dcount_q = s.query(D) \
            .filter(D.state == 'active')
        if org:
            dcount_q = dcount_q.join(
                O, O.id == D.owner_org).filter(O.name == org)
        if dataset:
            dcount_q = dcount_q.filter(or_(D.name == dataset,
                                           D.id == dataset,
                                           D.title == dataset))
        dcount = dcount_q.count()

        # datasets with errors
        derr = set()
        for res in q:
            out = check_url(res)
            if out:
                table.append(row_dict_norm(out))
                derr.add(out['dataset_id'])

        return {'table': table,
                'organization': org,
                'dataset': dataset,
                'marker': BROKEN_LINKS_MARKER,
                'total.datasets': dcount,
                'total.resources': count,
                'errors.datasets': len(derr),
                'errors.resources': len(table),
                }
    else:
        table = []

        for org_name in _get_organizations():
            if not org_name:
                continue
            report_args = {'org': org_name, 'dataset': None}
            data = get_report_data(report_args)
            if not data:
                raise ValueError("No report previously "
                                 "cached for {}"
                                 .format(BROKEN_LINKS_MARKER))

            row_stats = get_report_stats(data, org_name)
            table.append(row_dict_norm(row_stats))
        out = {u'table': table,
               u'organization': None,
               u'marker': BROKEN_LINKS_MARKER,
               }
        out.update(get_report_summary(table))
        return out


def reports_with_data(table):
    return [report for report in table if report[u'dataset_count']]


def tagless_dataset_optional_combination():
    organizations = _get_organizations()
    return [{u'org': org} for org in organizations]


def report_tagless_datasets(org):
    package_tag_ids = model.meta.Session.query(
        model.PackageTag.package_id).all()
    groups = model.meta.Session.query(model.Group)
    datasets = model.meta.Session.query(model.Package)
    table = [{
        u'organization': group.name,
        u'tagless_datasets': datasets.filter(
            ~model.Package.id.in_(package_tag_ids), model.Package.owner_org == group.id).count(),
        u'dataset_count': datasets.filter(model.Package.owner_org == group.id).count(),
        u'percentage_datasets_without_tags': calculate_report_percentage_by_org(
            datasets.filter(~model.Package.id.in_(
                package_tag_ids), model.Package.owner_org == group.id).count(),
            datasets.filter(model.Package.owner_org == group.id).count()
        ),
    } for group in groups]

    return {
        u'table': reports_with_data(table),
        u'dataset_checked': datasets.count(),
    }


def unpublished_dataset_options_combinations():
    organizations = _get_organizations()
    return [{u'org': org} for org in organizations]


def report_unpublished_dataset(org=None, dataset=None):
    groups = model.meta.Session.query(model.Group)
    datasets = model.meta.Session.query(model.Package)
    table = [{
        u'organization': group.name,
        u'unpublished_dataset_count': datasets.filter(
            model.Package.state != u'active', model.Package.owner_org == group.id).count(),
        u'dataset_count': datasets.filter(model.Package.owner_org == group.id).count(),
        u'percentage_unpublished_datasets': calculate_report_percentage_by_org(
            datasets.filter(model.Package.state != u'active',
                            model.Package.owner_org == group.id).count(),
            datasets.filter(model.Package.owner_org == group.id).count()
        ),
    } for group in groups]

    return {
        u'table': reports_with_data(table),
        u'dataset_checked': datasets.count(),
    }


def dataset_without_resources_options_combinations():
    organizations = _get_organizations()
    return [{u'org': org} for org in organizations]


def calculate_report_percentage_by_org(value, total):
    if value:
        return round((value / total) * 100, 2)
    return 0


def report_dataset_without_resources(org=None, dataset=None):
    groups = model.meta.Session.query(model.Group)
    datasets = model.meta.Session.query(model.Package)
    resources = model.meta.Session.query(model.Resource.package_id).all()
    table = [{
        u'organization': group.name,
        u'dataset_without_resource_count': datasets.filter(
            ~model.Package.id.in_(
                resources), model.Package.owner_org == group.id
        ).count(),
        u'dataset_count': datasets.filter(model.Package.owner_org == group.id).count(),
        u'percentage_dataset_without_resource': calculate_report_percentage_by_org(
            datasets.filter(
                ~model.Package.id.in_(resources), model.Package.owner_org == group.id).count(),
            datasets.filter(model.Package.owner_org == group.id).count()
        ),
    } for group in groups]

    return {
        u'table': reports_with_data(table),
        u'dataset_checked': datasets.count(),
    }


def all_reports():
    broken_link_info = {
        u'name': u'broken-links',
        u'description': _(u'List datasets with resources that are non-existent or return error response'),
        u'option_defaults': broken_links_options,
        u'generate': report_broken_links,
        u'option_combinations': broken_links_options_combinations,
        u'template': u'report/broken_links_report.html',
    }

    tagless_dataset_info = {
        u'name': u'tagless-dataset',
        u'description': _(u'List datasets without tags'),
        u'option_defaults': tagless_datasets_options,
        u'generate': report_tagless_datasets,
        u'option_combinations': tagless_dataset_optional_combination,
        u'template': u'report/tagless_dataset_report.html',
    }

    unpublished_dataset_info = {
        u'name': u'unpublished-dataset',
        u'description': _(u"List datasets that have not been published"),
        u'option_defaults': unpublished_dataset_options,
        u'generate': report_unpublished_dataset,
        u'option_combinations': unpublished_dataset_options_combinations,
        u'template': u'report/unpublished_dataset_report.html',
    }

    dataset_without_resources_info = {
        u'name': u'dataset-without-resources',
        u'description': _(u"List datasets that do not have resources"),
        u'option_defaults': dataset_without_resources_options,
        u'generate': report_dataset_without_resources,
        u'option_combinations': dataset_without_resources_options_combinations,
        u'template': u'report/dataset_without_resources_report.html',
    }

    return [
        broken_link_info,
        tagless_dataset_info,
        unpublished_dataset_info,
        dataset_without_resources_info,
    ]
