#!/bin/bash
## declare an array variable
declare -a arr=(
"money-printer"
"jonah"
"emily"
"john"
"bfserver"
"henry")


upload() {

    dest_path="~/mining"
    echo "$1"

    if [ "$1" = "bfserver" ]
    then
        dest_path="~/mining/gminer"
    fi

    # upload the python scripts
    scp -o IdentityFile=path *.py $1:$dest_path

    # upload requirements
    scp -o IdentityFile=path requirements.txt $1:$dest_path

    # install requirements then start the daemon
    ssh -tt $1 << EOF
                cd $dest_path
                source venv/bin/activate
                pip3 install -r requirements.txt
                exit
EOF
}

## now loop through the above array
for rig in "${arr[@]}"
do
    upload "$rig" &
done
wait
