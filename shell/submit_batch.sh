#!/bin/bash
#BSUB -W 10
#BSUB -n 40 
#BSUB -o out.%J
#BSUB -e err.%J

hostname -f

module load python
conda activate /usr/local/usrapps/[your_path]/metashape

python ${1} ${2}
# 1st arg is python script; 2nd is yaml config file

conda deactivate
