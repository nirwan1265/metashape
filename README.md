# Metashape Workflow

This space is intended to explain the proper workflow for Metaspace for image processing. The workflow will try to explain the steps required to run a basic Metashape workflow, i.e., build dense clouds, digital elevation model and orthomosaic patterns. It will use a python script to run as a batch job or as a parallel job.

## Requirements
* Python: Latest version of Python with [Anaconda distribution](https://www.anaconda.com/products/distribution).
* Metashape: Install the python module of Metashape using the [link](https://agisoft.freshdesk.com/support/solutions/articles/31000148930-how-to-install-metashape-stand-alone-python-module).
* Metashape license

## Usage

The script will run in the command line. An example command will look something like:
```
python <python_script.py> <config_file.yml>
```
The python script and the config file is in the repo. 

### Organizing Image Folders
There should be one main folder and subsequent sub-folders that contain all the photos from the flight mission to be processed. The ground control points (GCPs), should also be under the main folder. For exammple:
```
field_1 (main folder)
|------first_week (sub folder)
|         --img_001.tiff
|         --img_002.tiff
|         ...
|------second_week (sub folder)
|         --img_001.tiff
|         --img_002.tiff
|          ...
|------gcps (sub folder)
|          ...

field_2 (main folder)
|------first_week (sub folder)
|         --img_001.tiff
|         --img_002.tiff
|         ...
|------second_week (sub folder)
|         --img_001.tiff
|         --img_002.tiff
|          ...
|------gcps (sub folder)
|          ...

```

### Configurations
* **Parameters:** All the parameters explaining the Metashape configuration are explained in the YAML-format config file. This includes all the paths to the input and out files, quality filters, etc. 
* **Batch or Parallel Workflow:** A shell file that can run batch or parallel job is present in this repo. If you want to run jobs using different configurations, there is an R script that can combine "base" YAML file and a "derived" YAML file for each iterations.


## Creating a conda environment
Create a conda environment from a YAML file in the repo, using:
```
conda env create --prefix /usr/local/usrapps/[your_path]/metashape -f packages_metashape.yml
```
Activate the environment by using:
```
conda activate /usr/local/usrapps/[your_path]/metashape
```
Deactivate the environment by using:
```
conda deactivate
```



