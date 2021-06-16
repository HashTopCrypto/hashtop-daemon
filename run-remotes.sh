#!/bin/bash
## declare an array variable
declare -a arr=("money-printer"
"jonah"
"emily"
"john"
"bfserver"
"henry")

task() {
# create the tmux session if it doesnt already exist
    ssh -tt $1 << EOF
                    tmux new -A -d -s daemon
                    tmux detach -a
                    tmux detach
EOF
# kill daemon if its already running
    ssh -tt $1 "pkill -f main.py"

    # start the daemon up again in a tmux session
    ssh -tt $1 <<EOF
                    cd ~/mining
                    tmux send-keys -t "daemon" source Space venv/bin/activate  C-m
                    tmux send-keys -t "daemon" python3 Space main.py  C-m
                    exit
EOF
}

for rig in "${arr[@]}"
do 
    task "$rig" &
done
wait
