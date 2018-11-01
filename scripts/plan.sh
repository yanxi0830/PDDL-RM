#!/bin/bash

PLANNER=/home/xiyan/git/downward
TASK=$(cd "$(dirname "$1")"; pwd)/$(basename "$1")
TASK_DIR=$(cd "$(dirname "$1")"; pwd)
TASK_NAME="${TASK##*/}"
TASK_NAME=${TASK_NAME%.*}

echo 'Task PDDL: ' $TASK
echo $TASK_DIR
echo $PLANNER
echo $TASK_NAME

cd $PLANNER
./fast-downward.py --cleanup
./fast-downward.py --translate $TASK
./fast-downward.py --alias seq-sat-lama-2011 output.sas

head -n -1 ./sas_plan.1 > $TASK_DIR/$TASK_NAME.plan