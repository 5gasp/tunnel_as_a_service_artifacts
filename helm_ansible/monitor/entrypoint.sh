#!/bin/bash

# set the file path to wait for
file_path="/app/storage/config.env"

# loop until the file is present
while [ ! -f "$file_path" ]; do
    echo "File is not present waiting ..."
    sleep 1
done

# continue with the rest of the script once the file is present
echo "File $file_path is now present. Waiting for params in file..."
sleep 5
# read in the variables
set -o allexport
source $file_path
set +o allexport

export DOLLAR=$ 
# use envsubst to substitute the variables in the nginx config template
envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# start nginx with the modified configuration
nginx -g "daemon off;"    