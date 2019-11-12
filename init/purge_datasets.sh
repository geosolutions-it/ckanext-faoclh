SERVER=$1
APIKEY=$2

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

for dataset in $(curl ${SERVER}/api/3/action/package_list | jq -r '.["result"][]') ; do
  echo
  echo REMOVING DATASET $dataset

  curl ${SERVER}/api/3/action/dataset_purge \
      --data '{"id":"'$dataset'"}'  \
      -H "Content-Type:application/json" \
      -H "Authorization:${APIKEY}"
done
