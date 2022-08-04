# Metashape workflow

## Modules required:
import sys
import Metashape
import yaml
import metashape_functions as meta



#Running the Metashape workflow

doc, log, run_id = meta.project_setup(cfg)

meta.enable_and_log_gpu(log)


# only add photos if this is a brand new project, not based off an existing project
if cfg["load_project"] == "":  
    meta.add_photos(doc, cfg)

# Align photos
if cfg["alignPhotos"]["enabled"]:
    meta.align_photos(doc, log, cfg)
    meta.reset_region(doc)
 
# Adding GCPs
if cfg["addGCPs"]["enabled"]:
    meta.add_gcps(doc, cfg)
    meta.reset_region(doc)
 
# Building Dense Clouds
if cfg["buildDenseCloud"]["enabled"]:
    meta.build_dense_cloud(doc, log, run_id, cfg)
 
if cfg["buildDem"]["enabled"]:
    meta.build_dem(doc, log, run_id, cfg)

#Building Orthomosaic
if cfg["buildOrthomosaic"]["enabled"]:
    meta.build_orthomosaics(doc, log, run_id, cfg)

meta.export_report(doc, run_id, cfg)

meta.finish_run(log, config_file)
