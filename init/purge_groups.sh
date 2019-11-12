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

for json in groups/* ; do
  echo ===
  BASE=${json##*/}
  BARE=${BASE%.*}

  echo PURGING $BARE
  curl ${SERVER}/api/3/action/group_purge \
      --data '{"id":"'$BARE'"}'  \
      -H "Content-Type:application/json" \
      -H "Authorization:${APIKEY}"
done
