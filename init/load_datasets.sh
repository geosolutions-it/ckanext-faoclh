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
  cat $json |\
    jq 'del(.["groups"][]["id"])' |\
    jq '. += {"owner_org": .["organization"]["name"]}' |\
    jq 'del(.["organization"])'  |\
    jq '. += {"fao_resource_type": .["Q1"]}' |\
    jq '. += {"fao_activity_type": .["Q2"]}' |\
    jq '. += {"fao_geographic_focus": .["Q3"]}' |\
    jq '. += {"fao_release_year": .["custom_text"]}' > $NEW_JSON

#TODO: custom_resource_text

  curl ${SERVER}/api/3/action/package_create \
      --data @$NEW_JSON  \
      -H "Content-Type:application/json" \
      -H "Authorization:${APIKEY}"
done
