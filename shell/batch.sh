#!/bin/bash
hostname -f

module load python

python ${1} ${2}
# 1st arg is python script; 2nd is yaml config file

