#!/bin/bash
## declare an array variable
declare -a arr=(
"money-printer"
"jonah"
"emily"
#"john"
"bfserver"
"henry"
)


dest_path="~/mining/scripts"

job() {

    echo "$1"

    if [ "$1" = "bfserver" ]
    then
        dest_path="~/mining/gminer/scripts"
    fi

    # upload the python scripts
    scp -o IdentityFile=path ../*.py $1:$dest_path
    
    # upload requirements
    scp -o IdentityFile=path ../requirements.txt $1:$dest_path

    # install requirements and mark all shell scripts executable
    ssh -tt $1 << EOF
cd $dest_path
find . -iname "*.sh" -exec bash -c 'chmod +x "$0"' {} \;
source venv/bin/activate
pip3 install -r requirements.txt
exit
EOF
}

for rig in "${arr[@]}"
do
    job "$rig" &
done
wait
