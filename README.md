Requirements
============
CKAN 2.8.4+ (tested with CKAN 2.8.4)

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


Enable multilingual support
---------------------------

Enable multilingual support for datasets, organizations/groups, tags, and resources using the [ckanext-multilang](https://github.com/geosolutions-it/ckanext-multilang) extension by following the setup steps described below:
##### Clone and install the ckanext-multilang
- Navigate to CKAN's extension source directory
  ```
  $ cd /usr/lib/ckan/src/
  ```

- Clone ckanext-multilang 
  ```
  $ git clone https://github.com/geosolutions-it/ckanext-multilang
  ```

- Navigate to the ckanext-multilang root directory
  ```
  $ cd ckanext-multilang
  ```

- Activate CKAN's virtual environment
  ```
  $ . /usr/lib/ckan/default/bin/activate
  ```

- Install ckanext-multilang into CKAN's virtual environment
  ```
  $ pip install -e .
  ```

##### Configure multilingual support in CKAN's configuration file (production.ini)

To add multilingual configurations in CKAN's configuration file `production.ini` (found at `/etc/ckan/default/production.ini`), add the following configuration:

- Add ckanext-multilang extensions using the `ckan.plugins` configuration key separating each extension by space.  
  Read more about adding extension [here](https://docs.ckan.org/en/2.8/extensions/tutorial.html#creating-a-new-extension).
  ```
  ckan.plugins = [...] multilang [...]
  ```

 - Add all locales you intend to use in the user interface using `ckan.locales_offered` configuration key by adding space-separated locale codes.  
   Read more about CKAN's internationalization settings [here](https://docs.ckan.org/en/2.8/extensions/translating-extensions.html).
 
   For example, to add English, and French, use the sample configuration below:
   ```
   ckan.locales_offered = en fr
   ```

- Enable the tag localization adding the line:

  ```
  multilang.enable_tag_localization = True
  ```


##### Initialize the database with the mandatory tables needed for localized records:
Make sure the virtual environment is active before running the command below. See previous steps on how to activate the virtual environment.
```
$ paster --plugin=ckanext-multilang multilangdb initdb --config=/etc/ckan/default/production.ini
```

##### Update the Solr schema.xml file used by CKAN introducing the following elements.
Update the schema.xml file (located at `/usr/lib/ckan/src/ckan/ckan/config/solr/schema.xml`) with the following xml tags:

- Inside the `fields` tags, add the tag below:
  ```
  <dynamicField name="package_multilang_localized_*" type="text" indexed="true" stored="true" multiValued="false"/>
  ```

- Add the `copyField` tag shown below:
  ```
  <copyField source="package_multilang_localized_*" dest="text"/>
  ```

- Restart Solr
  ```
  $ sudo service solr restart
  ```

- Restart CKAN
  ```
  $ systemctl restart supervisord
  ```

Initialize database tables
==========================

To initialize database tables, follow the steps below

Activate the virtual environment

    $ . /usr/lib/ckan/default/bin/activate


Create database tables by running the command below

    $ paster --plugin=ckanext-faoclh initdb --config=/etc/ckan/default/production.ini



Configuring CKAN for CSV export
===============================

CKAN allows you to create jobs that run in the ‘background’, i.e. asynchronously and without blocking the main application.

Background jobs can be essential to providing certain kinds of functionality, for example:
* Generate a CSV dataset export file asynchronously.
* Creating webhooks that notify other services when certain changes occur (for example a dataset is updated)

Basically, any piece of work that takes too long to perform while the main application is waiting is a good candidate for a background job. Read more about CKAN's background job [here](https://docs.ckan.org/en/2.8/maintaining/background-tasks.html)

To enable CKAN's background jobs in [ckanext-faoclh](https://github.com/geosolutions-it/ckanext-faoclh), create a file name `ckan-worker.ini` in `/etc/supervisord.d/` then copy in the code below.

    # =======================================================
    # Supervisor configuration for CKAN background job worker
    # =======================================================
    
    [program:ckan-worker]
    # Use the full paths to the virtualenv and your configuration file here.
    command=/usr/lib/ckan/default/bin/paster --plugin=ckan jobs worker --config=/etc/ckan/default/production.ini
    
    user=ckan
    
    # Start just a single worker. Increase this number if you have many or
    # particularly long running background jobs.
    numprocs=1
    process_name=%(program_name)s-%(process_num)02d
    
    # Log files.
    stdout_logfile=/var/log/ckan/worker.log
    stderr_logfile=/var/log/ckan/worker.err
    
    # Make sure that the worker is started on system start and automatically
    # restarted if it crashes unexpectedly.
    autostart=true
    autorestart=true
    
    # Number of seconds the process has to run before it is considered to have
    # started successfully.
    startsecs=10
    
    # Need to wait for currently executing tasks to finish at shutdown.
    # Increase this if you have very long running tasks.
    stopwaitsecs = 600

Create a directory to hold all the generated CSV datasets and grant user 'ckan' permissions to it. You may need root privileges to do that.  
Let's say we want to use `/var/lib/ckan/export':

    $ mkdir /var/lib/ckan/export
    $ chown ckan: /var/lib/ckan/export


Add the created directory to CKAN configuration file (`/etc/ckan/default/production.ini`) using the `faoclh.export_dataset_dir` settings key as shown below

    faoclh.export_dataset_dir = /var/lib/ckan/export


Once the file is  created, restart CKAN using the command below:

    $ systemctl restart supervisord


#### To run asynchronous worker in dev environment using the command below
```
$ paster --plugin=ckan jobs worker --config=/etc/ckan/default/production.ini
```


Loading initial data
====================

These steps are needed to load initial groups, organizations, dataset, vocabularies.  

This initial setup is only needed one time, when the app is deployed for the first time.


Load default groups
-------------------

Enter in the `bin/` directory.

Run

    ./load_groups.sh SERVER_URL API_KEY
    
E.g.

    ./load_groups.sh http://10.10.100.136 b973eae2-33c2-4e06-a61f-4b1ed71d277c
   
In order to remove the groups:

    ./purge_groups.sh SERVER_URL API_KEY
    
Please note that groups image names changed over time, so if you already have your groups and the images are not properly loaded, please consider editing the groups info and setting the filenames according to the [actual files](https://github.com/geosolutions-it/ckanext-faoclh/tree/master/ckanext/faoclh/public/fao/images/group).


Load default organizations
--------------------------

Enter in the `bin/` directory.

Run

    ./load_orgs.sh SERVER_URL API_KEY
    
E.g.

    ./load_orgs.sh http://10.10.100.136 b973eae2-33c2-4e06-a61f-4b1ed71d277c   


Load vocabularies
-----------------

The default vocabulary files are in `init/vocab/`.
    
Make sure the virtualenv is active, and then load the vocabularies (double check and fix the vocab paths):

- `paster --plugin=ckanext-faoclh vocab load -i /etc/ckan/default/vocab/fao_resource_type.json     --config=/etc/ckan/default/production.ini`
- `paster --plugin=ckanext-faoclh vocab load -i /etc/ckan/default/vocab/fao_activity_type.json     --config=/etc/ckan/default/production.ini`
- `paster --plugin=ckanext-faoclh vocab load -i /etc/ckan/default/vocab/fao_geographic_focus.json  --config=/etc/ckan/default/production.ini`

_**Next lines are about an old file-based vocabularies handling. They are only valid if you didn't edit your vocab items in the CKAN GUI.**_

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

Enabling Tracking
==============
To enable page view tracking, follow the steps below:
- Set `ckan.tracking_enabled` to true in the `[app:main]` section of your CKAN configuration file (production.ini found at `/etc/ckan/default/production.ini`)

Save the file and restart your web server. CKAN will now record raw page view tracking data in your CKAN database as pages are viewed.


for example:
```
[app:main]
ckan.tracking_enabled = true
```
- Setup a cron job to update the tracking summary data.

For operations based on the tracking data CKAN uses a summarised version of the data, not the raw tracking data that is recorded “live” as page views happen. The `paster tracking update` and `paster search-index rebuild` commands need to be run periodicially to update this tracking summary data.


You can setup a cron job to run these commands. On most UNIX systems you can setup a cron job by running `crontab -e` in a shell to edit your crontab file, and adding a line to the file to specify the new job. For more information run `man crontab` in a shell. For example, here is a crontab line to update the tracking data and rebuild the search index hourly:

```
@hourly /usr/lib/ckan/default/bin/paster --plugin=ckan tracking update -c /etc/ckan/default/production.ini && /usr/lib/ckan/default/bin/paster --plugin=ckan search-index rebuild -r -c /etc/ckan/default/production.ini
```


The `@hourly` can be replaced with `@daily`, `@weekly` or `@monthly`.

## Retrieving Tracking Data
Run the command below to generate a csv file with tracking data:
```
paster --plugin=ckan tracking export "/path/to/csv/file/tracking.csv" "2020-01-01" --config=/etc/ckan/default/production.ini
```

> **NOTE**: Replace "2020-01-01" with an offset date from which the tracking data will generate.
