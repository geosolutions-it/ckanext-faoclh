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

Enable multilingual support
============

Enable multilingual support for datasets, organizations/groups, tags, and resources using the [ckanext-multilang](https://github.com/geosolutions-it/ckanext-multilang) extension by following the setup steps described below:

#### Clone and install the [ckanext-spatial](https://github.com/ckan/ckanext-spatial) that is required by ckanext-multilang
- Navigate to CKAN's source directory
```
$ cd /usr/lib/ckan/src/
```

- Clone ckanext-spatial
```
$ git clone https://github.com/ckan/ckanext-spatial
```

- Navigate to the ckanext-spatial root directory

```
$ cd ckanext-spatial
```

- Activate CKAN's virtual environment
```
$ . /usr/lib/ckan/default/bin/activate
```

- Install ckanext-spatial into CKAN's virtual environment
```
$ pip install -e .
```

### Clone and install the ckanext-multilang
- Navigate to CKAN's source directory
```
$ cd /usr/lib/ckan/src/
```

- Clone ckanext-spatial
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

- Install ckanext-spatial into CKAN's virtual environment
```
$ pip install -e .
```

### Initialize the database with the mandatory tables needed for localized records:
```
$ paster --plugin=ckanext-multilang multilangdb initdb --config=/etc/ckan/default/production.ini
```

NOTE: Make sure that the virtual environment is active before running the above command. See previous steps on how to activate the virtual environment.

### Configure multilingual support in CKAN's configuration file (production.ini)
To add multilingual configurations in CKAN's configuration file (production.ini) found at `/etc/ckan/default/production.ini`, add the following configuration keys:

- Add ckanext-spatial, ckanext-multilang extensions using the `ckan.plugins` configuration key separating each extension by space. Read more about adding extension [here](https://docs.ckan.org/en/ckan-1.4.3/extensions.html).
```
ckan.plugins = ckanext-spatial ckanext-multilang
```

 - Add all locales you intend to use in the user interface using `ckan.locales_offered` configuration key by adding space-separated locale codes. Read more about CKAN's internationalization settings [here](https://docs.ckan.org/en/ckan-2.7.3/maintaining/configuration.html#internationalisation-settings).
 
 For example, to add English, and French, use the sample configuration below:
```
ckan.locales_offered = en fr
```

### Update the Solr schema.xml file used by CKAN introducing the following elements.
Update the schema.xml file (located at `/usr/lib/ckan/src/ckan/ckan/config/solr/schema.xml`) with the following xml tags:

Inside the `fields` tags, add the tag below:
```
<dynamicField name="package_multilang_localized_*" type="text" indexed="true" stored="true" multiValued="false"/>
```

Add the `copyField` tag shown below:
```
<copyField source="package_multilang_localized_*" dest="text"/>
```

Restart Solr
```
$ sudo service solr restart
```

### Restart CKAN
```
$ systemctl restart supervisord
```


