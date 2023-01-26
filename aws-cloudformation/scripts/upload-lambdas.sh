#!/bin/bash

P_DIR=./packages
for ff in $(find $P_DIR -type f -maxdepth 1 -name "*.zip") ; do 
    echo $ff;
    f=$(echo $ff | awk -F/ '{print $NF}');
    echo Uploading $f to $1/$2;

    if [ "$2" == "/" ]; then
        echo "Root bucket prefix ";
        aws s3api put-object --bucket $1 --key $f --body $ff --profile $3;
        aws s3api put-object-acl --bucket $1 --key $f --acl $4 --profile $3;
    else
        echo "Using $2 bucket prefix";
        aws s3api put-object --bucket $1 --key $2/$f --body $ff --profile $3;
        aws s3api put-object-acl --bucket $1 --key $2/$f --acl $4 --profile $3;
    fi
done