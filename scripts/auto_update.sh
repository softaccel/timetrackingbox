#!/bin/bash

wget -q --spider https://github.com/softaccel/timetrackingbox

if [ $? -eq 0 ]; then
    cd /usr/lib/python3.7
    git clone https://github.com/softaccel/timetrackingbox

    diff -q -r Spalek timetrackingbox

    if [ $? -eq 0 ]; then
        echo "No content change"
    else
        cp Spalek Spalek.bak -r
        rm Spalek -r

        cp timetrackingbox Spalek -r
    fi

    rm timetrackingbox -r

else
    echo "Offline"
    exit
fi
