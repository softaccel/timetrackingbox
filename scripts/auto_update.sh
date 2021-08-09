#!/bin/bash

wget -q --spider https://github.com/softaccel/timetrackingbox

if [ $? -eq 0 ]; then
    cd /usr/lib/python3.7
    git clone https://github.com/softaccel/timetrackingbox

    diff -q -r Spalek timetrackingbox

    if [ $? -eq 0 ]; then
        echo "No content change"

        rm timetrackingbox -r
    else
        rm Spalek.bak -r
        mv Spalek Spalek.bak

        mv timetrackingbox Spalek
    fi

else
    echo "Offline"
    exit
fi
