Requirements
============
CKAN 2.8.3+ (tested with CKAN 2.8.3)

ckanext-faoclh
==============

Available plugins:

- `faoclh`: 


Configuration
-------------

Install the extension:
```
pip install -e .
```


Load default groups
-------------------

Enter in the `bin/` directory.

Run

    ./load_groups.sh SERVER_URL API_KEY
    
E.g.    

    ./load_groups.sh http://10.10.100.136 b973eae2-33c2-4e06-a61f-4b1ed71d277c   
   
In order to remove the groups:

    ./purge_groups.sh SERVER_URL API_KEY


Load default organizations
--------------------------

Enter in the `bin/` directory.

Run

    ./load_orgs.sh SERVER_URL API_KEY
    
E.g.    

    ./load_orgs.sh http://10.10.100.136 b973eae2-33c2-4e06-a61f-4b1ed71d277c   


Setup vocabulary files path
---------------------------

Edit your `.ini` file and add the `fao.vocab.path` property, setting it to whatever directory
contains the vocabularies.

The default vocabulary files are in `init/vocab/`, so you may set the directory exported with git.
Anyway, if you want to edit your vocabularies and make sure a new deploy of the extension won't 
overwrite your customization, you may want to copy the files in another dir, let's say
`/etc/ckan/default/vocab`.

So your line in `production.ini` would be like this: 

    fao.vocab.path = /etc/ckan/default/vocab
    
Then activate the virtualenv and load the vocabularies:

- `paster --plugin=ckanext-faoclh vocab load -i /etc/ckan/default/vocab/fao_resource_type.json     --config=/etc/ckan/default/production.ini`
- `paster --plugin=ckanext-faoclh vocab load -i /etc/ckan/default/vocab/fao_activity_type.json     --config=/etc/ckan/default/production.ini`
- `paster --plugin=ckanext-faoclh vocab load -i /etc/ckan/default/vocab/fao_geographic_focus.json  --config=/etc/ckan/default/production.ini`

If you need to update the vocabulary, edit the file and run the `vocab load` command again; the
command will add and remove the related tags as needed.

If you need to completely remove a vocabulary, you can run:

    paster --plugin=ckanext-faoclh vocab delete -n VOCAB_NAME --config=/etc/ckan/default/production.ini

for instance

    paster --plugin=ckanext-faoclh vocab delete -n fao_resource_type --config=/etc/ckan/default/production.ini
 

Load datasets
-------------

Enter in the `bin/` directory.

Run

    ./load_datasets.sh SERVER_URL API_KEY
    
E.g.    

    ./load_dataset.sh http://10.10.100.136 b973eae2-33c2-4e06-a61f-4b1ed71d277c   

This step requires that groups and organizations have already been created.

Enabling Reporting
================
Enable reporting of broken Links, tagless dataset, dataset without resources, unpublished datasets using the [ckanext-gsreport](https://github.com/geosolutions-it/ckanext-gsreport) CKAN extension by following the setup steps described below:
> **NOTE**: [ckanext-gsreport](https://github.com/geosolutions-it/ckanext-gsreport) depends on [ckanex-report](https://github.com/davidread/ckanext-report) CKAN extension and [OWSLib](https://pypi.org/project/OWSLib/)

- Activate CKAN virtual environment.
```
$ . /usr/lib/ckan/default/bin/activate
```
- Install [ckanext-report](https://github.com/davidread/ckanext-report) CKAN extension.
```
$ pip install -e git+https://github.com/datagovuk/ckanext-report.git#egg=ckanext-report
```

- Install [OWSLib](https://pypi.org/project/OWSLib/) python library.
```
$ pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org OWSLib==0.10.3
```

- Navigate to ckanext-faoclh src directory, clone and Install [ckanext-gsreport](https://github.com/geosolutions-it/ckanext-gsreport).
```
$ cd /usr/lib/ckan/src/
```

```
$ git clone https://github.com/geosolutions-it/ckanext-gsreport.git
```

```
$ cd ckanext-gsreport & pip install -e .
```

- Add `status_reports`, `ckanext-reports` extensions to CKAN config file (`production.ini` found at `/etc/ckan/default/production.ini`) using the `ckan.plugins` configuration key separating each extension by space and save the file.
Add status_reports to plugins. 
> **Note**: Order of entries matters. This `status_reports` should be placed before report plugin as shown below.
```
ckan.plugins = ... status_reports report
```

- Initialize `ckanext-reports` database.
```
$ paster --plugin=ckanext-report report initdb --config=/etc/ckan/default/production.ini
```

- Run solr data reindexing (license and resource format reports are using special placeholders in solr to access data without value):
```
$ paster --plugin=ckan search-index rebuild_fast -c /etc/ckan/default/production.ini
```

- Generate reports

The reports can be generated in two ways:

 * in CLI (this can be used to set up cron job):
  
   * generate all reports:
```
$ paster --plugin=ckanext-report report generate --config=/etc/ckan/default/production.ini
```

   * generate one report
```
$ paster --plugin=ckanext-report report generate $report-name --config=/etc/ckan/default/production.ini
```

> **NOTE**: This can take a while to produce results. Especially broken-links report may take a significant amount of time because it will check each resource for availability.

At this point, you can navigate to `/report` route in the CKAN user interface and view the generated reports

- Set up a crone job to generate reports
Set up a crone job to generate reports You can set up a cron job to run these commands. On most UNIX systems you can set up a cron job by running `crontab -e` in a shell to edit your crontab file, and adding a line to the file to specify the new job. For more information run `man crontab` in a shell. For example, here is a crontab line to generate the reports daily:
```
@daily /usr/lib/ckan/default/bin/paster --plugin=ckanext-report report generate --config=/etc/ckan/default/production.ini
```
The `@daily` can be replaced with `@hourly`, `@weekly` or `@monthly`.
