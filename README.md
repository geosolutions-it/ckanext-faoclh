# ckanext-faoclh

This extension adds customizations for the FAO-CLH deploy.

Available plugins:

- `faoclh`: 

## Requirements

CKAN 2.8.4+ (tested with CKAN 2.8.4)


# Installation and Update 

Activate virtualenv then install the extension, as user ckan:

    $ cd /usr/lib/ckan/src/
    $ git clone https://github.com/geosolutions-it/ckanext-faoclh ## or this one in case of deployment in the FAO server: git clone https://tdipisa@bitbucket.org/cioapps/ckanext-faoclh.git
    $ cd ckanext-faoclh/
    $ pip install -e .

To update an already installed faoclh extension, as user ckan:

    $ cd /usr/lib/ckan/src/ckanext-faoclh/
    $ git pull
    $ pip install -e . ## only if required, it depends on the entity of the update 

	
Activate virtualenv for other eventual installation steps of other involved extensions in the faoclh deploy.

## Init DB 

The following command is needed for the upload of custom images for vocabulary items

    $ paster --plugin=ckanext-faoclh initdb --config=/etc/ckan/default/production.ini

## Update the Solr schema 

Update the schema.xml file (located at `/usr/lib/ckan/src/ckan/ckan/config/solr/schema.xml`) with the following xml tags:

- Inside the `fields` tags, add the tag below:

      <field name="fao_resource_type" type="string" indexed="true" stored="true" multiValued="true"/>
    
## Enable multilingual support

Enable multilingual support for datasets, organizations/groups, tags, and resources using the [ckanext-multilang](https://github.com/geosolutions-it/ckanext-multilang) extension by following the setup steps described below:

### [multilang] Clone and install the extension

- Navigate to CKAN's extension source directory:

  ```
  $ cd /usr/lib/ckan/src/
  ```

- Clone ckanext-multilang:

  ```
  $ git clone https://github.com/geosolutions-it/ckanext-multilang
  ```

- Navigate to the ckanext-multilang root directory:

  ```
  $ cd ckanext-multilang
  ```

- Activate CKAN's virtual environment:

  ```
  $ . /usr/lib/ckan/default/bin/activate
  ```

- Install ckanext-multilang into CKAN's virtual environment:

  ```
  $ pip install -e .
  ```

### [multilang] Configure multilingual support

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
   ckan.locales_offered = en es fr
   ```
   
   Below the complete configuration for languages
   
    ```
   ckan.locale_default = en
   ckan.locale_order = en es fr
   ckan.locales_offered = en es fr
   ckan.locales_filtered_out = en_GB 
   ```
	 
- Enable the tag localization adding the line:

  ```
  multilang.enable_tag_localization = False
  ```

### [multilang] Initialize the database

Make sure the virtual environment is active before running the command below. See previous steps on how to activate the virtual environment.

    $ paster --plugin=ckanext-multilang multilangdb initdb --config=/etc/ckan/default/production.ini


### [multilang] Update the Solr schema

Update the schema.xml file (located at `/usr/lib/ckan/src/ckan/ckan/config/solr/schema.xml`) with the following xml tags:

- Inside the `fields` tags, add the tag below:

  ```
  <dynamicField name="package_multilang_localized_*" type="text" indexed="true" stored="true" multiValued="false"/>
  ```

- Add the `copyField` tag shown below:

  ```
  <copyField source="package_multilang_localized_*" dest="text"/>
  ```

- Restart Solr:

      sudo service solr restart

- Restart CKAN:

      systemctl restart supervisord


## Enable filtering by "year of release"

To enable filtering of datasets by custom resource field "year of release" follow the steps described below:

- Add the line below in `production.ini` (found at /etc/ckan/default/production.ini) to enable indexing of the custom resource field "year of release"
 
    ```
    ckan.extra_resource_fields = custom_resource_text
    ```
	
- Restart CKAN

- Reindex:

```
$ paster --plugin=ckan search-index rebuild  --config=/etc/ckan/default/production.ini
```

## Initialize database tables	

To initialize database tables for the fao-clh extension, follow the steps below.	

Activate the virtual environment:	

    $ . /usr/lib/ckan/default/bin/activate	

Create database tables by running the command below:

    $ paster --plugin=ckanext-faoclh initdb --config=/etc/ckan/default/production.ini


## Configuring CKAN for CSV export

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
Let's say we want to use `/var/lib/ckan/export`:

    mkdir /var/lib/ckan/export
    chown ckan: /var/lib/ckan/export


Add the created directory to CKAN configuration file (`/etc/ckan/default/production.ini`) using the `faoclh.export_dataset_dir` settings key as shown below

    faoclh.export_dataset_dir = /var/lib/ckan/export 


Once the file is  created, restart CKAN using the command below:

    systemctl restart supervisord

To run asynchronous worker in dev environment using the command below

    paster --plugin=ckan jobs worker --config=/etc/ckan/default/production.ini


## Enabling CKAN Tracking

To enable page view tracking, follow the steps below:

- Set `ckan.tracking_enabled` to true in the `[app:main]` section of your CKAN configuration file (production.ini found at `/etc/ckan/default/production.ini`)

      [app:main]
      ckan.tracking_enabled = true

- Save the file and restart CKAN: CKAN will now record raw page view tracking data in your CKAN database as pages are viewed.
	
- Setup a cron job to update the tracking summary data.

For operations based on the tracking data CKAN uses a summarised version of the data, not the raw tracking data that is recorded “live” as page views happen. The `paster tracking update` and `paster search-index rebuild` commands need to be run periodicially to update this tracking summary data.

You can setup a cron job to run these commands. On most UNIX systems you can setup a cron job by running `crontab -e` in a shell to edit your crontab file, and adding a line to the file to specify the new job. For more information run `man crontab` in a shell. 
Below is a crontab line to update the tracking data and rebuild the search index. As root, in /etc/crontab add line:

    0 * * * * ckan /usr/lib/ckan/default/bin/paster --plugin=ckan tracking update -c /etc/ckan/default/production.ini && /usr/lib/ckan/default/bin/paster --plugin=ckan search-index rebuild -r -c /etc/ckan/default/production.ini

From command line:

    service crond reload

	
### Retrieving Tracking Data

Run the command below to generate a csv file with tracking data:

    paster --plugin=ckan tracking export "/path/to/csv/file/tracking.csv" "2020-01-01" --config=/etc/ckan/default/production.ini 


> **NOTE**: Replace "2020-01-01" with an offset date from which the tracking data will generate.


## Tracking data access with Google Analytics

Send tracking data to google analytics using the [ckanext-googleanalytics](https://github.com/ckan/ckanext-googleanalytics) 
extension by following the steps below.

- Activate CKAN's virtual environment

      . /usr/lib/ckan/default/bin/activate
	
- Install [ckanext-googleanalytics](https://github.com/ckan/ckanext-googleanalytics)

      git clone https://github.com/ckan/ckanext-googleanalytics.git
      cd ckanext-googleanalytics
      pip install -e  .
      pip install -r  requirements.txt
      pip install future

- Add the `googleanalytics` plugin in the `ckan.plugins` configuration key, separating each extension by space.   

      ckan.plugins = [...] googleanalytics

- Create GA tables:
 
      paster --plugin=ckanext-googleanalytics initdb -c /etc/ckan/default/production.ini
      
- Edit your ckan .ini file to provide these necessary parameters:

      googleanalytics.id = UA-XXXXXX-1
      googleanalytics.account = Account name (i.e. data.gov.uk, see top level item at https://www.google.com/analytics)
      googleanalytics.username = googleaccount@gmail.com
      googleanalytics.password = googlepassword
      googleanalytics.show_downloads = true
	
> **Note**: Your password will probably be readable by other people; so you may want to set up a 
  new Gmail account with [2fa](https://www.google.com/landing/2step/) enabled specifically for accessing your Gmail profile.

- Restart CKAN to enable google analytics
  
      systemctl restart supervisord


## Enable dataset rating

Enable dataset rating using [ckanext-rating](https://github.com/geosolutions-it/ckanext-rating.git) by following the steps below.

- Activate CKAN's virtual environment:

    ```
    $ . /usr/lib/ckan/default/bin/activate
    ```
- Install [ckanext-rating](https://github.com/geosolutions-it/ckanext-rating.git):

```
	$ cd /usr/lib/ckan/src/
	$ git clone https://github.com/geosolutions-it/ckanext-rating.git
	$ cd ckanext-rating/
	$ pip install -e .
```
	
- Initialize database tables used by ckanext-rating

    ```
    $ paster --plugin=ckanext-rating rating init --config=/etc/ckan/default/production.ini
    ```
	
- Add the `rating` plugin by editing the `ckan.plugins` property in the CKAN config file (e.g. `production.ini` found at `/etc/ckan/default/production.ini`):

    ```
    ckan.plugins = [...] rating
    ```

> **TIP**: Enabled/disabled ratings for unauthenticated users using `rating.enabled_for_unauthenticated_users` configuaration key as shown below
      
```
rating.enabled_for_unauthenticated_users = true or false
```
      
- Restart CKAN

Optionally, list dataset types for which the rating will be shown (defaults to ['dataset']) using the `ckanext.rating.enabled_dataset_types` settings key.

## Enable comments

Enable user commenting functionality on datasets using [ckanext-ytp-comments](https://github.com/geosolutions-it/ckanext-ytp-comments.git) by following the steps below:

- Activate CKAN's virtual environment

    ```
    $ . /usr/lib/ckan/default/bin/activate
    ```
	
- Install [ckanext-ytp-comments](https://github.com/geosolutions-it/ckanext-ytp-comments.git)

```
	$ cd /usr/lib/ckan/src/
        $ git clone https://github.com/geosolutions-it/ckanext-ytp-comments.git
	$ cd ckanext-ytp-comments/
	$ git checkout faoclh
	$ pip install -e .
        $ pip install -r requirements.txt
```
	
- Add the `ytp_comments` plugin by editing the `ckan.plugins` property in the CKAN config file (`production.ini` found at `/etc/ckan/default/production.ini`):

    ```
    ckan.plugins = [...] ytp_comments
    ```
	
- Initialize database tables used by ckanext-ytp-comments

    ```
    $ paster --plugin=ckanext-ytp-comments initdb --config=/etc/ckan/default/production.ini
    ```

- Restart CKAN

## Resource Preview plugins

### Datastore plugin

Some preview plugins require the data to be stored in the `datastore` plugin. 

Create postgres user and DB:
 
    sudo -u postgres createuser -S -D -R -P -l datastore_default    
    sudo -u postgres createdb -O ckan_default datastore_default -E utf-8
    
Edit CKAN `ini` file:
- uncomment the following lines and edit the password accordingly:    

      ckan.datastore.write_url = postgresql://CKAN_USER:CKAN_USER_PW@localhost/datastore_default
      ckan.datastore.read_url = postgresql://datastore_default:DATASTORE_PW@localhost/datastore_default
      
- enable the datastore plugin

      ckan.plugins = [...] datastore [...]      

Set the permissions on the database:
    
    paster --plugin=ckan datastore set-permissions -c /etc/ckan/default/development.ini | sudo -u postgres psql --set ON_ERROR_STOP=1

### Datapusher

The datapusher plugin parses data files and loads the parsed data into the datastore  

The datapusher is implemented as an external WSGI service, plus a plugin inside CKAN to interact with it.

#### Datapusher WSGI application

- Create a virtualenv for datapusher

      virtualenv /usr/lib/ckan/datapusher

- Create a source directory and switch to it

      mkdir /usr/lib/ckan/datapusher/src
      cd /usr/lib/ckan/datapusher/src

- Clone the source (latest tagged version at the moment [2020-07-29] is 0.0.17)
    
      sudo git clone -b 0.0.17 https://github.com/ckan/datapusher.git
    
  In version 0.0.17 the apache2/wsgi configuration has changed a bit, so we have the relevant configuration file in 
  this extension (ckanext-faoclh), in the directory `deploy/datapusher`.     

- Install the DataPusher and its requirements

      cd datapusher
      . /usr/lib/ckan/datapusher.bin7activate
      pip install -r requirements.txt
      python setup.py develop

- Copy WSGI configuration files:

      mkdir /etc/ckan/datapusher
      cp -v /usr/lib/ckan/src/ckanext-faoclh/deploy/datapusher/datapusher* /etc/ckan/datapusher

- As root, make sure the WSGI module is installed:

      apt install libapache2-mod-wsgi

- As root, create config file for apache2 and enable it:

      sudo cp /usr/lib/ckan/src/ckanext-faoclh/deploy/datapusher/050-datapusher.conf /etc/apache2/sites-available/050-datapusher.conf
      sudo a2ensite 050-datapusher

      sudo service apache2 restart
     

#### Datapusher plugin

Enable the datapusher plugin

    ckan.plugins = [...] datastore [...] datapusher [...]      

Add the datapusher service URL in the CKAN `ini` file:

    ckan.datapusher.url = http://0.0.0.0:8800/

### Preview plugins

In the ckan configuration `ini` file, make sure there are these plugins in the `ckan.plugins` line: 
- `text_view`: Displays files in XML, JSON or plain text
- `image_view`: If the resource format is a common image format like PNG, JPEG, or GIF, it adds `<img>` tags 
                pointing to the resource URL
- `webpage_view`: Adds `<iframe>` tags to embed the resource URL.                 
- `recline_view`: Adds a rich widget, based on the [Recline](https://github.com/okfn/recline/) Javascript library.       
   This plugin requires the `datastore` plugin to be installed (and configured)
- `resource_proxy`: Allows view plugins access to external files not localted in the CKAN server.

### PDF view

PDF preview needs an external library.

- Install the library:

      . /usr/lib/ckan/default/bin/activate
      pip install ckanext-pdfview

- Edit CKAN `ini` file and add the `pdf_view` plugin:

      ckan.plugins = [...] pdf_view [...]

### Create views for datasets

Make sure that in the CKAN `ini` file the `default_views` property contains all the views we want to create previews for:

    ckan.views.default_views = image_view text_view recline_view pdf_view

If you add plugin views in an already populated CKAN instance, you have to add the missing views to the datasets 
resources:  

   - After activating the CKAN virtualenv, run:   

         paster  --plugin=ckan views create -c /etc/ckan/default/production.ini 
         
## Enabling Reporting

Enable reporting of broken Links, tagless dataset, dataset without resources, unpublished datasets.

> **NOTE**: [ckanext-faoclh](https://github.com/geosolutions-it/ckanext-faoclh) depends on 
> [ckanext-report](https://github.com/davidread/ckanext-report) CKAN extension 
> and [OWSLib](https://pypi.org/project/OWSLib/) for reporting

- Activate CKAN virtual environment:

      . /usr/lib/ckan/default/bin/activate

- Install [ckanext-report](https://github.com/davidread/ckanext-report) CKAN extension:

      pip install -e git+https://github.com/datagovuk/ckanext-report.git#egg=ckanext-report

- Install [OWSLib](https://pypi.org/project/OWSLib/) python library:

      pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org OWSLib==0.10.3

- Add `ckanext-reports` plugin to the line `ckan.plugins` in the CKAN config file (`production.ini`);
  (**Note**: Order of entries matters. The `faoclh` pluing should be placed before `report` plugin as shown below):

      ckan.plugins = [...] faoclh report [...] 

- Initialize `ckanext-reports` database:

      paster --plugin=ckanext-report report initdb --config=/etc/ckan/default/production.ini

- Run solr data reindexing (license and resource format reports are using special placeholders in solr to access data without value):

      paster --plugin=ckan search-index rebuild_fast -c /etc/ckan/default/production.ini

### Generating reports

Using the command line, you can issue this command to generate all reports:

    paster --plugin=ckanext-report report generate -c /etc/ckan/default/production.ini

If you need a single report, use this line::

    paster --plugin=ckanext-report report generate $report-name -c /etc/ckan/default/production.ini

> **NOTE**: The command can take a while to produce results. Especially broken-links report may take a significant amount of time because it will check each resource for availability.

### Setting up a cron job to generate reports

In order to have reports regularly generated, you may want to run the previous command via cron.

Edit file `/etc/crontab` and add the line

    0  *    * * *   ckan    /usr/lib/ckan/default/bin/paster --plugin=ckanext-report report generate -c /etc/ckan/default/production.ini

You may alter the job periodicity at will; the current value will generate reports at midnight every day.

Then have `cron` reload its configuration file:

    service cron reload


### Accessing reports

You can navigate to `/report` route in the CKAN user interface to view the generated reports.



## Loading initial data

These steps are needed to load initial groups, organizations, dataset, vocabularies.  

This initial setup is only needed one time, when the app is deployed for the first time.


### Load default groups

Enter in the `bin/` directory.

Run

```
./load_groups.sh SERVER_URL API_KEY
```
	
E.g.

```
./load_groups.sh http://10.10.100.136 b973eae2-33c2-4e06-a61f-4b1ed71d277c
```
	
In order to remove the groups:
	
```
./purge_groups.sh SERVER_URL API_KEY
```
	
Please note that groups image names changed over time, so if you already have your groups and the images are not properly loaded, please consider editing the groups info and setting the filenames according to the [actual files](https://github.com/geosolutions-it/ckanext-faoclh/tree/master/ckanext/faoclh/public/fao/images/group).


### Load default organizations

Enter in the `bin/` directory.

Run

```
./load_orgs.sh SERVER_URL API_KEY
```
E.g.

```
./load_orgs.sh http://10.10.100.136 b973eae2-33c2-4e06-a61f-4b1ed71d277c   
```

### Load vocabularies

The default vocabulary files are in `init/vocab/`.
    
Make sure the virtualenv is active, and then load the vocabularies (double check and fix the vocab paths):

- `paster --plugin=ckanext-faoclh vocab load -i /etc/ckan/default/vocab/fao_resource_type.json     --config=/etc/ckan/default/production.ini`
- `paster --plugin=ckanext-faoclh vocab load -i /etc/ckan/default/vocab/fao_activity_type.json     --config=/etc/ckan/default/production.ini`
- `paster --plugin=ckanext-faoclh vocab load -i /etc/ckan/default/vocab/fao_geographic_focus.json  --config=/etc/ckan/default/production.ini`

_**Next lines are about an old file-based vocabularies handling. They are only valid if you didn't edit your vocab items in the CKAN GUI.**_

If you need to update the vocabulary, edit the file and run the `vocab load` command again; the
command will add and remove the related tags as needed.

If you need to completely remove a vocabulary, you can run:

    $ paster --plugin=ckanext-faoclh vocab delete -n VOCAB_NAME --config=/etc/ckan/default/production.ini


for instance

    $ paster --plugin=ckanext-faoclh vocab delete -n fao_resource_type --config=/etc/ckan/default/production.ini

### Load datasets

Enter in the `bin/` directory.

Run

```
./load_datasets.sh SERVER_URL API_KEY
```
	
E.g.

```
./load_dataset.sh http://10.10.100.136 b973eae2-33c2-4e06-a61f-4b1ed71d277c
```
	
This step requires that groups and organizations have already been created.


### Further setup

CKAN by default does not clean up the session cache files. Cache files are stored in a subdir of the `/tmp` direcotory; 
If your server is not rebooted every few days, the session files may fill up the inode space, and the system may become unstable.

Edit file `/etc/crontab` and add the line

    0  *    * * *   ckan    find /tmp/faoclh/sessions/ -mmin +1440 -type f -print -exec rm {} \;

Then have `cron` reload its configuration file:

    service cron reload

