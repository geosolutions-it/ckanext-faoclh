#!/bin/bash

SERVER=$1
APIKEY=$2

NEW_JSON=/tmp/load_dataset.json

function usage() {
  echo $0 SERVER APIKEY
}

if [ -z "$SERVER" ]
then
  echo "Missing parameter"
  usage
  exit 1
fi

if [ -z "$APIKEY" ]
then
  echo "Missing parameter"
  usage
  exit 1
fi

for json in datasets/* ; do
  echo ===
  echo UPLOADING $json
#  sed -e s=__SERVER__=$SERVER=g $json > $NEW_JSON
  export Q1=$(cat $json | jq -r '.["Q1"]' | sed "s/ /_/g" | sed "s_/_-_g" )
  export Q2=$(cat $json | jq -r '.["Q2"]' | sed "s/ /_/g" | sed "s_/_-_g" )
  export Q3=$(cat $json | jq -r '.["Q3"]' | sed "s/ /_/g" | sed "s_/_-_g" )

  echo Q1 is $Q1
  echo Q2 is $Q2
  echo Q3 is $Q3

  cat $json |\
    jq 'del(.["groups"][]["id"])' |\
    jq '. += {"owner_org": .["organization"]["name"]}' |\
    jq 'del(.["organization"])'  |\
    jq 'if .["Q1"] then . += {"fao_resource_type":    [env.Q1]} else . end' |\
    jq 'if .["Q2"] then . += {"fao_activity_type":    [env.Q2]} else . end' |\
    jq 'if .["Q3"] then . += {"fao_geographic_focus": [env.Q3]} else . end' |\
    jq '. += {"fao_release_year": .["custom_text"]}' > $NEW_JSON

    # cp $NEW_JSON /tmp/$(basename $json)
    # cat $NEW_JSON
    # exit

#TODO: custom_resource_text

  curl ${SERVER}/api/3/action/package_create \
      --data @$NEW_JSON  \
      -H "Content-Type:application/json" \
      -H "Authorization:${APIKEY}"
done
