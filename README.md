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


Load datasets
-------------

Enter in the `bin/` directory.

Run

    ./load_datasets.sh SERVER_URL API_KEY
    
E.g.    

    ./load_dataset.sh http://10.10.100.136 b973eae2-33c2-4e06-a61f-4b1ed71d277c   

This step requires that groups and organizations have already been created.




