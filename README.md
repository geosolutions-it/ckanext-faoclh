# ckanext-faoclh

This extension adds customizations for the FAO-CLH deploy.

Available plugins:

- `faoclh`: 

## Requirements

CKAN 2.8.4+ (tested with CKAN 2.8.4)


# Installation and Update 

Activate virtualenv then install the extension, as user ckan:

```
$ cd /usr/lib/ckan/src/
$ git clone https://github.com/geosolutions-it/ckanext-faoclh ## or this one in case of deployment in the FAO server: git clone https://tdipisa@bitbucket.org/cioapps/ckanext-faoclh.git
$ cd ckanext-faoclh/
$ pip install -e .

## The following command is needed for the upload of custom images for vocabulary items
$ paster --plugin=ckanext-faoclh initdb --config=/etc/ckan/default/production.ini
```

To update an already installed faoclh extension, as user ckan:

```
$ cd /usr/lib/ckan/src/ckanext-faoclh/
$ git pull
$ pip install -e . ## only if required, it depends on the entity of the update 
```
	
Activate virtualenv for other eventual installation steps of other involved extensions in the faoclh deploy.

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

```
$ paster --plugin=ckanext-multilang multilangdb initdb --config=/etc/ckan/default/production.ini 
```

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

  ```
  $ sudo service solr restart
  ```

- Restart CKAN:

  ```
  $ systemctl restart supervisord
  ```

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

```
$ . /usr/lib/ckan/default/bin/activate	
```

Create database tables by running the command below:

```
$ paster --plugin=ckanext-faoclh initdb --config=/etc/ckan/default/production.ini	
```
	
## Configuring CKAN for CSV export

CKAN allows you to create jobs that run in the ‘background’, i.e. asynchronously and without blocking the main application.

Background jobs can be essential to providing certain kinds of functionality, for example:
* Generate a CSV dataset export file asynchronously.
* Creating webhooks that notify other services when certain changes occur (for example a dataset is updated)

Basically, any piece of work that takes too long to perform while the main application is waiting is a good candidate for a background job. Read more about CKAN's background job [here](https://docs.ckan.org/en/2.8/maintaining/background-tasks.html)

To enable CKAN's background jobs in [ckanext-faoclh](https://github.com/geosolutions-it/ckanext-faoclh), create a file name `ckan-worker.ini` in `/etc/supervisord.d/` then copy in the code below.

```
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
```

Create a directory to hold all the generated CSV datasets and grant user 'ckan' permissions to it. You may need root privileges to do that.  
Let's say we want to use `/var/lib/ckan/export`:

```
$ mkdir /var/lib/ckan/export
$ chown ckan: /var/lib/ckan/export
```
    
Add the created directory to CKAN configuration file (`/etc/ckan/default/production.ini`) using the `faoclh.export_dataset_dir` settings key as shown below

```
faoclh.export_dataset_dir = /var/lib/ckan/export 
```
	
Once the file is  created, restart CKAN using the command below:

```
$ systemctl restart supervisord
```
    
To run asynchronous worker in dev environment using the command below

```
$ paster --plugin=ckan jobs worker --config=/etc/ckan/default/production.ini
```
	
## Enabling CKAN Tracking

To enable page view tracking, follow the steps below:

- Set `ckan.tracking_enabled` to true in the `[app:main]` section of your CKAN configuration file (production.ini found at `/etc/ckan/default/production.ini`)

```
[app:main]
ckan.tracking_enabled = true
```

- Save the file and restart CKAN: CKAN will now record raw page view tracking data in your CKAN database as pages are viewed.
	
- Setup a cron job to update the tracking summary data.

For operations based on the tracking data CKAN uses a summarised version of the data, not the raw tracking data that is recorded “live” as page views happen. The `paster tracking update` and `paster search-index rebuild` commands need to be run periodicially to update this tracking summary data.

You can setup a cron job to run these commands. On most UNIX systems you can setup a cron job by running `crontab -e` in a shell to edit your crontab file, and adding a line to the file to specify the new job. For more information run `man crontab` in a shell. 
Below is a crontab line to update the tracking data and rebuild the search index. As root, in /etc/crontab add line:
	
```
0 * * * * ckan /usr/lib/ckan/default/bin/paster --plugin=ckan tracking update -c /etc/ckan/default/production.ini && /usr/lib/ckan/default/bin/paster --plugin=ckan search-index rebuild -r -c /etc/ckan/default/production.ini
```

From command line:

```
$ service crond reload
```
	
### Retrieving Tracking Data

Run the command below to generate a csv file with tracking data:

```
$ paster --plugin=ckan tracking export "/path/to/csv/file/tracking.csv" "2020-01-01" --config=/etc/ckan/default/production.ini 
```
	
> **NOTE**: Replace "2020-01-01" with an offset date from which the tracking data will generate.


## Tracking data access with Google Analytics

Send tracking data to google analytics using the [ckanext-googleanalytics](https://github.com/ckan/ckanext-googleanalytics) extension by following the steps below.

- Activate CKAN's virtual environment

    ```
    $ . /usr/lib/ckan/default/bin/activate
    ```
	
- Install [ckanext-googleanalytics](https://github.com/ckan/ckanext-googleanalytics)

    ```
    $ pip install -e  git+https://github.com/ckan/ckanext-googleanalytics.git#egg=ckanext-googleanalytics
    ```

- Add the `googleanalytics` plugin in the `ckan.plugins` configuration key, separating each extension by space.   

    ```
    ckan.plugins = [...] googleanalytics
    ```

- Edit your ckan .ini file to provide these necessary parameters:

    ```
    googleanalytics.id = UA-XXXXXX-1
    googleanalytics.account = Account name (i.e. data.gov.uk, see top level item at https://www.google.com/analytics)
    googleanalytics.username = googleaccount@gmail.com
    googleanalytics.password = googlepassword
    googleanalytics.show_downloads = true
    ```
	
> **Note**: Your password will probably be readable by other people; so you may want to set up a 
  new Gmail account with [2fa](https://www.google.com/landing/2step/) enabled specifically for accessing your Gmail profile.

- Restart CKAN to enable google analytics
  
    ```
    $ systemctl restart supervisord
    ```

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

```
$ paster --plugin=ckanext-faoclh vocab delete -n VOCAB_NAME --config=/etc/ckan/default/production.ini
```
	
for instance

```
$ paster --plugin=ckanext-faoclh vocab delete -n fao_resource_type --config=/etc/ckan/default/production.ini
```

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

## Enabling Common Resource Preview Tools

The CKAN resource page can contain one or more visualizations of the resource data or file contents (a table, a bar chart, a map, etc). These are commonly referred to as resource views. Different view types are implemented via custom plugins, which can be activated on a particular CKAN site. To enable a resource views, add them by editing the `ckan.plugins` property in the CKAN config file (production.ini found at `/etc/ckan/default/production.ini`) as shown below and restart CKAN:
```
ckan.plugins = [...] image_view recline_view pdf_view [...]
```
The main features of resource views are:
- One resource can have multiple views of the same data (for example a grid and some graphs for tabular data).
- Dataset editors can choose which views to show, reorder them and configure them individually.
- Individual views can be embedded on external sites.

Whether a particular resource can be rendered by the different view plugins is decided by the view plugins themselves. This is generally done checking the resource format or whether its data is on the [DataStore extension](https://docs.ckan.org/en/2.8/maintaining/datastore.html) or not.

From the management interface you can create and edit views manually, to automatically create resource types whenever a new resource is created/updated, add them by editing the `ckan.views.default_views` property in the CKAN config file (production.ini found at `/etc/ckan/default/production.ini`) as shown below and restart CKAN:
```
ckan.views.default_views = [...] recline_view pdf_view geojson_view [...]
```
Below is a description of how to set up some common resource preview formats. Some do not require further setup and can be directly added to the `ckan.plugins` setting without necessarily installing custom plugins.

### Text view
Displays files in XML, JSON or plain text based formats with the syntax highlighted. The formats detected can be configured using the [ckan.preview.xml_formats](https://docs.ckan.org/en/2.8/maintaining/configuration.html#ckan-preview-xml-formats), [ckan.preview.json_formats](https://docs.ckan.org/en/2.8/maintaining/configuration.html#ckan-preview-json-formats) and [ckan.preview.text_formats](https://docs.ckan.org/en/2.8/maintaining/configuration.html#ckan-preview-text-formats) configuration options respectively.

If you want to display files that are hosted in a different server from your CKAN instance (e.g that haven’t been uploaded to CKAN) you will need to enable the [Resource Proxy](#resource-proxy) plugin.

Enable the text resource views by adding `text_view` plugin to CKAN's `ckan.plugins` configuaration key in `/etc/ckan/default/production.ini` as shown below and restart CKAN:
```
ckan.plugins = [...] text_view [...]
```
### Image view
If the resource format is a common image format like PNG, JPEG or GIF, it adds an `<img>` tag pointing to the resource URL. You can provide an alternative URL on the edit view form. The available formats can be configured using the [ckan.preview.image_formats](https://docs.ckan.org/en/2.8/maintaining/configuration.html#ckan-preview-image-formats) configuration option.

Enable the image resource views by adding `image_view` plugin to CKAN's `ckan.plugins` configuaration key in `/etc/ckan/default/production.ini` as shown below and restart CKAN:
```
ckan.plugins = [...] image_view [...]
```

### Web page view
Adds an `<iframe>` tag to embed the resource URL. You can provide an alternative URL on the edit view form.

Enable the web page resource views by adding `webpage_view` plugin to CKAN's `ckan.plugins` configuaration key in `/etc/ckan/default/production.ini` as shown below then restart:
```
ckan.plugins = [...] webpage_view [...]
```

### PDF view
Renders PDF resources using [PDF.js](https://github.com/mozilla/pdf.js#online-demo). Enable PDF resource view by following the steps described below:
- Activate CKAN's virtual environment
```
 . /usr/lib/ckan/default/bin/activate
```
- Install [ckanext-pdfview](https://github.com/ckan/ckanext-pdfview)
```
$ pip install ckanext-pdfview
```
- Add `pdf_view` to the `ckan.plugins` setting in your CKAN config file (`production.ini` found at `/etc/ckan/default/production.ini`) as shown below and restart CKAN:
```
 ckan.plugins = [...] pdf_view [...]
```

If you want to render PDF files which are not located in the same server as CKAN you also need to enable the [resource_proxy](#resource-proxy) plugin.

### Data Explorer
Adds a rich widget, based on the [Recline](https://github.com/okfn/recline/) Javascript library. It allows querying, filtering, graphing and mapping data. The Data Explorer is optimized for displaying structured data hosted on the [DataStore](https://docs.ckan.org/en/2.8/maintaining/datastore.html) extension.

The Data Explorer can also display certain formats of tabular data (CSV and Excel files) without its contents being uploaded to the DataStore. This is done via the [DataProxy](https://github.com/okfn/dataproxy), an external service that will parse the contents of the file and return a response that the view widget understands. However, as the resource must be downloaded by the [DataProxy](https://github.com/okfn/dataproxy) service and parsed before it is viewed, this option is slower and less reliable than viewing data that is in the [DataStore](https://docs.ckan.org/en/2.8/maintaining/datastore.html). It also does not properly support different encodings, proper field type detection, etc so users are strongly encouraged to host data on the [DataStore](https://docs.ckan.org/en/2.8/maintaining/datastore.html) instead.

Enable the data explorer resource views by adding `recline_view` to the `ckan.plugins` setting in your CKAN config file (`production.ini` found at `/etc/ckan/default/production.ini`) as shown below and restart CKAN:
```
 ckan.plugins = [...] recline_view [...]
```

### DataStore Grid
Displays a filterable, sortable, table view of structured data. This plugin requires data to be in the [DataStore](https://docs.ckan.org/en/2.8/maintaining/datastore.html).

Enable the datastore grid resource views by adding `recline_grid_view` to the `ckan.plugins` setting in your CKAN config file (`production.ini` found at `/etc/ckan/default/production.ini`) as shown below and restart CKAN:
```
 ckan.plugins = [...] recline_grid_view [...]
```

### DataStore Graph
Allows to create graphs from data stored on the DataStore. You can choose the graph type (such as lines, bars, columns, etc) and restrict the displayed data, by filtering by a certain field value or defining an offset and the number of rows. This plugin requires data to be in the [DataStore](https://docs.ckan.org/en/2.8/maintaining/datastore.html).

Enable the datastore graph resource views by adding `recline_graph_view` to the `ckan.plugins` setting in your CKAN config file (`production.ini` found at `/etc/ckan/default/production.ini`) as shown below and restart CKAN:
```
 ckan.plugins = [...] recline_graph_view [...]
```

### DataStore Map
Shows data stored on the [DataStore](https://docs.ckan.org/en/2.8/maintaining/datastore.html) in an interactive map. It supports plotting markers from a pair of latitude / longitude fields or from a field containing a [GeoJSON](https://geojson.org/) representation of the geometries. The configuration also allows to cluster markers if there is a high density of them and to zoom automatically to the rendered features. This plugin requires data to be in the [DataStore](https://docs.ckan.org/en/2.8/maintaining/datastore.html).

There is partial support to change the map tiles to a different service, such as Mapbox. Look below for an example to add to your configuration file:
```
# Mapbox example:
ckanext.spatial.common_map.type = mapbox
ckanext.spatial.common_map.mapbox.map_id = <id>
ckanext.spatial.common_map.mapbox.access_token = <token>
ckanext.spatial.common_map.attribution=© <a target=_blank href='https://www.mapbox.com/map-feedback/'>Mapbox</a> © <a target=_blank href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a>
ckanext.spatial.common_map.subdomains = <subdomains>

# Custom example:
ckanext.spatial.common_map.type = custom
ckanext.spatial.common_map.custom.url = <url>
ckanext.spatial.common_map.custom.tms = <tms>
ckanext.spatial.common_map.attribution = <copyright link>
ckanext.spatial.common_map.subdomains = <subdomains>
```

Enable the datastore map resource views by adding `recline_map_view` to the `ckan.plugins` setting in your CKAN config file (`production.ini` found at `/etc/ckan/default/production.ini`) as shown below and restart CKAN:
```
 ckan.plugins = [...] recline_map_view [...]
```

### Resource Proxy
As resource views are rendered on the browser, if the file they are accessing is located in a different domain than the one CKAN is hosted, the browser will block access to it because of the same-origin policy. For instance, files hosted on `www.example.com` won’t be able to be accessed from the browser if CKAN is hosted on `data.catalog.com`.

To allow view plugins access to external files you need to activate the `resource_proxy` plugin on your configuration file:

Enable the resource proxy by adding `resource_proxy` to the `ckan.plugins` setting in your CKAN config file (`production.ini` found at `/etc/ckan/default/production.ini`) as shown below:
```
 ckan.plugins = [...] resource_proxy [...]
```
