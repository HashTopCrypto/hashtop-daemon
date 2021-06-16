#!/bin/bash
## declare an array variable
declare -a arr=("money-printer"
"jonah"
"emily"
"john"
"bfserver"
"henry")

task() {
    daemon_path="~/mining"
    echo "$1"

    if [ "$1" = "bfserver" ]
    then
        daemon_path="~/mining/gminer"
    fi

# create the tmux session if it doesnt already exist
    #ssh -tt $1 << EOF
 #                   tmux new -A -d -s daemon
#EOF
# kill daemon if its already running
    ssh -tt $1 "pkill -f main.py"

    # start the daemon up again in a tmux session
    ssh -tt $1 <<EOF
                    tmux send-keys -t mining:1 cd Space $daemon_path  C-m
                    tmux send-keys -t mining:1 source Space venv/bin/activate  C-m
                    tmux send-keys -t mining:1 python3 Space main.py  C-m
                    tmux send-keys -t mining:1 tmux Space detach Space -a C-m
                    exit
EOF
}

for rig in "${arr[@]}"
do 
    task "$rig" &
done
wait
