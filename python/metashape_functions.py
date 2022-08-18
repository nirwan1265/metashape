# Import Modules
import time
import datetime
import platform
import os
import glob
import re
import yaml
import Metashape
import read_yaml

# Function for project setup 
sep = "; "

def stamp_time():
    '''
    Format the timestamps as needed
    '''
    stamp = datetime.datetime.now().strftime('%Y%m%dT%H%M')
    return stamp

def diff_time(t2, t1):
    '''
    Give a end and start time, subtract, and round
    '''
    total = str(round(t2-t1, 1))
    return total

def project_setup(cfg):
    '''
    Creating project and output paths.
    Defining project IDs and time stamps
    Defining log files
    '''
    
    #Make project folders, if it doesn't exists
    if not os.path.exists(cfg["output_path"]):
        os.makedirs(cfg["output_path"])
    if not os.path.exists(cfg["project_path"]):
        os.makedirs(cfg["project_path"])
    
    ### Set a filename template for project and output files
    ### The photoset ID and location string for filename
    
    run_name = cfg["run_name"]
    
    
    ## Project file example: "projectID_YYYMMDDtHHMM-jobID.psx"
    timestamp = stamp_time()
    run_id = "_".join([run_name,timestamp])
    
    project_file = os.path.join(cfg["project_path"], '.'.join([run_id, 'psx']) )
    log_file = os.path.join(cfg["output_path"], '.'.join([run_id+"_log",'txt']) )
    
    
    '''
    Create a doc and a chunk
    '''
    
    #Create a handle to the Metashape object
    doc = Metashape.Document()
    #While running via Metashape, can use: doc = Metashape.app.document
    
    # If specified, open existing project
    if cfg["load_project"] != "":
        doc.open(cfg["load_project"])
    else:
        chunk = doc.addChunk()
        chunk.crs = Metashape.CoordinateSystem(cfg["project_crs"])
        #chunk.marker_crs = Metashape.CoordinateSystem(cfg["addGCPs"]["gcf_crs"])
        
    
    # Save doc as a new project regardless of old or new project
    doc.save(projec_file)
    
    
    
    '''
    Log Specs except for GPU
    '''
    
    # log Metashape version, CPU specs, time, and project location to results file
    # open the results file
    # TODO: records the Slurm values for actual cpus and ram allocated
    # https://slurm.schedmd.com/sbatch.html#lbAI
    with open(log_file, 'a') as file:

        # write a line with the Metashape version
        file.write(sep.join(['Project', run_id])+'\n')
        file.write(sep.join(['Agisoft Metashape Professional Version', Metashape.app.version])+'\n')
        # write a line with the date and time
        file.write(sep.join(['Processing started', stamp_time()]) +'\n')
        # write a line with CPU info - if possible, improve the way the CPU info is found / recorded
        file.write(sep.join(['Node', platform.node()])+'\n')
        file.write(sep.join(['CPU', platform.processor()]) +'\n')
        # write two lines with GPU info: count and model names - this takes multiple steps to make it look clean in the end

    return doc, log_file, run_id
    
def add_photos(doc, cfg):
    '''
    Add photos to project and change their labels to include their containing folder
    '''
    
    ## Get all the paths to the project photos
    a = glob.iglob(os.path.join(cfg["photo_path"],"**","*.*"), recursive = True) #(([jJ][pP][gG])|([tT][iI][fF]))
    b = [path for path in a]
    photo_files = [x for x in b if (re.search("(.tif$)|(.jpg$)|(.TIF$)|(.JPG*)",x) and (not re.search("dem_usgs.tif",x)))]
    
    ##Add them
    ## Add them
    if cfg["multispectral"]:
        doc.chunk.addPhotos(photo_files, layout = Metashape.MultiplaneLayout)
    else:
        doc.chunk.addPhotos(photo_files)
    
    doc.save()
    
    return True
    
def align_photos(doc, log_file, cfg):
    '''
    Match photos, align cameras, optimize cameras
    '''
    
    ### Align photos, align cameras, optimize cameras
    
    # Get the starting time stamp
    timer1a = time.time()
    
    # Align cameras
    doc.chunk.matchPhotos(downscale=cfg["alignPhotos"]["downscale"],
                          subdivide_task = cfg["subdivide_task"])
    doc.chunk.alignCameras(adaptive_fitting=cfg["alignPhotos"]["adaptive_fitting"],
                           subdivide_task = cfg["subdivide_task"])
    doc.save()
    
    # Get an ending time stamp
    timer1b = time.time()

    # calculate difference between end and start time to 1 decimal place
    time1 = diff_time(timer1b, timer1a)
    
    # record results to file
    with open(log_file, 'a') as file:
        file.write(sep.join(['Align Photos', time1])+'\n')

    return True

def reset_region(doc):
    '''
    Reset the region and make it much larger than the points; necessary because if points go outside the region, they get clipped when saving
    '''

    doc.chunk.resetRegion()
    region_dims = doc.chunk.region.size
    region_dims[2] *= 3
    doc.chunk.region.size = region_dims

    return True

def build_dense_cloud(doc, log_file, run_id, cfg):
    '''
    Build depth maps and dense cloud
    '''

    ### Build depth maps

    # get a beginning time stamp for the next step
    timer2a = time.time()

    # build depth maps only instead of also building the dense cloud ##?? what does
    doc.chunk.buildDepthMaps(downscale=cfg["buildDenseCloud"]["downscale"],
                             filter_mode=cfg["buildDenseCloud"]["filter_mode"],
                             reuse_depth=cfg["buildDenseCloud"]["reuse_depth"],
                             max_neighbors=cfg["buildDenseCloud"]["max_neighbors"],
                             subdivide_task=cfg["subdivide_task"])
    doc.save()

    # get an ending time stamp for the previous step
    timer2b = time.time()

    # calculate difference between end and start time to 1 decimal place
    time2 = diff_time(timer2b, timer2a)

    # record results to file
    with open(log_file, 'a') as file:
        file.write(sep.join(['Build Depth Maps', time2]) + '\n')

    ### Build dense cloud

    # get a beginning time stamp for the next step
    timer3a = time.time()

    # build dense cloud
    doc.chunk.buildDenseCloud(max_neighbors=cfg["buildDenseCloud"]["max_neighbors"],
                              keep_depth = cfg["buildDenseCloud"]["keep_depth"],
                              subdivide_task = cfg["subdivide_task"],
                              point_colors = True)
    doc.save()

    # get an ending time stamp for the previous step
    timer3b = time.time()

    # calculate difference between end and start time to 1 decimal place
    time3 = diff_time(timer3b, timer3a)

    # record results to file
    with open(log_file, 'a') as file:
        file.write(sep.join(['Build Dense Cloud', time3])+'\n')

    ### Classify ground points


    if cfg["buildDenseCloud"]["classify"]:

        # get a beginning time stamp for the next step
        timer_a = time.time()

        doc.chunk.dense_cloud.classifyGroundPoints(max_angle=cfg["buildDenseCloud"]["max_angle"],
                                                   max_distance=cfg["buildDenseCloud"]["max_distance"],
                                                   cell_size=cfg["buildDenseCloud"]["cell_size"])
        doc.save()

        # get an ending time stamp for the previous step
        timer_b = time.time()

        # calculate difference between end and start time to 1 decimal place
        time_tot = diff_time(timer_b, timer_a)

        # record results to file
        with open(log_file, 'a') as file:
            file.write(sep.join(['Classify Ground Points', time_tot]) + '\n')



    ### Export points

    if cfg["buildDenseCloud"]["export"]:

        output_file = os.path.join(cfg["output_path"], run_id + '_points.las')

        if cfg["buildDenseCloud"]["classes"] == "ALL":
            # call without classes argument (Metashape then defaults to all classes)
            doc.chunk.exportPoints(path=output_file,
                                   source_data=Metashape.DenseCloudData,
                                   format=Metashape.PointsFormatLAS,
                                   crs=Metashape.CoordinateSystem(cfg["project_crs"]),
                                   subdivide_task=cfg["subdivide_task"])
        else:
            # call with classes argument
            doc.chunk.exportPoints(path=output_file,
                                   source_data=Metashape.DenseCloudData,
                                   format=Metashape.PointsFormatLAS,
                                   crs=Metashape.CoordinateSystem(cfg["project_crs"]),
                                   clases=cfg["buildDenseCloud"]["classes"],
                                   subdivide_task=cfg["subdivide_task"])

    return True
 
 
def build_dem(doc, log_file, run_id, cfg):
        '''
        Build end export DEM
        '''

        # get a beginning time stamp for the next step
        timer5a = time.time()

        #prepping params for buildDem
        projection = Metashape.OrthoProjection()
        projection.crs = Metashape.CoordinateSystem(cfg["project_crs"])

        #prepping params for export
        compression = Metashape.ImageCompression()
        compression.tiff_big = cfg["buildDem"]["tiff_big"]
        compression.tiff_tiled = cfg["buildDem"]["tiff_tiled"]
        compression.tiff_overviews = cfg["buildDem"]["tiff_overviews"]

        if (cfg["buildDem"]["type"] == "DSM") | (cfg["buildDem"]["type"] == "both"):
            # call without classes argument (Metashape then defaults to all classes)
            doc.chunk.buildDem(source_data = Metashape.DenseCloudData,
                               subdivide_task = cfg["subdivide_task"],
                               projection = projection)
            output_file = os.path.join(cfg["output_path"], run_id + '_dsm.tif')
            if cfg["buildDem"]["export"]:
                doc.chunk.exportRaster(path=output_file,
                                       projection=projection,
                                       nodata_value=cfg["buildDem"]["nodata"],
                                       source_data=Metashape.ElevationData,
                                       image_compression=compression)
        if (cfg["buildDem"]["type"] == "DTM") | (cfg["buildDem"]["type"] == "both"):
            # call with classes argument
            doc.chunk.buildDem(source_data = Metashape.DenseCloudData,
                               classes = Metashape.PointClass.Ground,
                               subdivide_task = cfg["subdivide_task"],
                               projection = projection)
            output_file = os.path.join(cfg["output_path"], run_id + '_dtm.tif')
            if cfg["buildDem"]["export"]:
                doc.chunk.exportRaster(path=output_file,
                                       projection=projection,
                                       nodata_value=cfg["buildDem"]["nodata"],
                                       source_data=Metashape.ElevationData,
                                       image_compression=compression)
        if (cfg["buildDem"]["type"] != "DTM") & (cfg["buildDem"]["type"] == "both") & (cfg["buildDem"]["type"] == "DSM"):
            raise ValueError("DEM type must be either 'DSM' or 'DTM' or 'both'")

        doc.save()

        # get an ending time stamp for the previous step
        timer5b = time.time()

        # calculate difference between end and start time to 1 decimal place
        time5 = diff_time(timer5b, timer5a)

        # record results to file
        with open(log_file, 'a') as file:
            file.write(sep.join(['Build DEM', time5])+'\n')

        return True

# This is just a helper function called by build_orthomosaic
def export_orthomosaic(doc, log_file, run_id, cfg):
    '''
    Export orthomosaic
    '''



    return True


def build_export_orthomosaic(doc, log_file, run_id, cfg, file_ending):
    '''
    Helper function called by build_orthomosaics. build_export_orthomosaic builds and exports an ortho based on the current elevation data.
    build_orthomosaics sets the current elevation data and calls build_export_orthomosaic (one or more times depending on how many orthomosaics requested)
    '''

    # get a beginning time stamp for the next step
    timer6a = time.time()

    #prepping params for buildDem
    projection = Metashape.OrthoProjection()
    projection.crs = Metashape.CoordinateSystem(cfg["project_crs"])

    doc.chunk.buildOrthomosaic(surface_data=Metashape.ElevationData,
                               blending_mode=cfg["buildOrthomosaic"]["blending"],
                               fill_holes=cfg["buildOrthomosaic"]["fill_holes"],
                               refine_seamlines=cfg["buildOrthomosaic"]["refine_seamlines"],
                               subdivide_task=cfg["subdivide_task"],
                               projection=projection)

    doc.save()

    ## Export orthomosaic
    if cfg["buildOrthomosaic"]["export"]:
        output_file = os.path.join(cfg["output_path"], run_id + '_ortho_' + file_ending + '.tif')

        compression = Metashape.ImageCompression()
        compression.tiff_big = cfg["buildOrthomosaic"]["tiff_big"]
        compression.tiff_tiled = cfg["buildOrthomosaic"]["tiff_tiled"]
        compression.tiff_overviews = cfg["buildOrthomosaic"]["tiff_overviews"]

        projection = Metashape.OrthoProjection()
        projection.crs = Metashape.CoordinateSystem(cfg["project_crs"])

        doc.chunk.exportRaster(path=output_file,
                               projection=projection,
                               nodata_value=cfg["buildOrthomosaic"]["nodata"],
                               source_data=Metashape.OrthomosaicData,
                               image_compression=compression)

    # get an ending time stamp for the previous step
    timer6b = time.time()

    # calculate difference between end and start time to 1 decimal place
    time6 = diff_time(timer6b, timer6a)

    # record results to file
    with open(log_file, 'a') as file:
        file.write(sep.join(['Build Orthomosaic', time6]) + '\n')

    return True

def build_orthomosaics(doc, log_file, run_id, cfg):
    '''
    Build orthomosaic. This function just calculates the needed elevation data(s) and then calls build_export_orthomosaic to do the actual building and exporting. It does this multiple times if orthos based on multiple surfaces were requsted
    '''

    # prep projection for export step below (in case export is enabled)
    projection = Metashape.OrthoProjection()
    projection.crs = Metashape.CoordinateSystem(cfg["project_crs"])

    # get a beginning time stamp for the next step
    timer6a = time.time()

    # what should the orthomosaic filename end in? e.g., DSM, DTM, USGS to indicate the surface it was built on
    file_ending = cfg["buildOrthomosaic"]["surface"]

    # Import USGS DEM as surface for orthomosaic if specified
    if cfg["buildOrthomosaic"]["surface"] == "USGS":
        path = os.path.join(cfg["photo_path"],cfg["buildOrthomosaic"]["usgs_dem_path"])
        crs = Metashape.CoordinateSystem(cfg["buildOrthomosaic"]["usgs_dem_crs"])
        doc.chunk.importRaster(path=path,
                               crs=crs,
                               raster_type=Metashape.ElevationData)
        build_export_orthomosaic(doc, log_file, run_id, cfg, file_ending = "USGS")
    # Otherwise use Metashape point cloud to build elevation model
    # DTM: use ground points only
    if (cfg["buildOrthomosaic"]["surface"] == "DTM") | (cfg["buildOrthomosaic"]["surface"] == "DTMandDSM"):
        doc.chunk.buildDem(source_data = Metashape.DenseCloudData,
                           classes=Metashape.PointClass.Ground,
                           subdivide_task=cfg["subdivide_task"],
                           projection=projection)
        build_export_orthomosaic(doc, log_file, run_id, cfg, file_ending = "dtm")
    # DSM: use all point classes
    if (cfg["buildOrthomosaic"]["surface"] == "DSM") | (cfg["buildOrthomosaic"]["surface"] == "DTMandDSM"):
        doc.chunk.buildDem(source_data = Metashape.DenseCloudData,
                           subdivide_task=cfg["subdivide_task"],
                           projection=projection)
        build_export_orthomosaic(doc, log_file, run_id, cfg, file_ending = "dsm")

    return True
 
def export_report(doc, run_id, cfg):
    '''
    Export report
    '''

    output_file = os.path.join(cfg["output_path"], run_id+'_report.pdf')

    doc.chunk.exportReport(path = output_file)

    return True


def finish_run(log_file,config_file):
    '''
    Finish run (i.e., write completed time to log)
    '''

    # finish local results log and close it for the last time
    with open(log_file, 'a') as file:
        file.write(sep.join(['Run Completed', stamp_time()])+'\n')

    # open run configuration again. We can't just use the existing cfg file because its objects had already been converted to Metashape objects (they don't write well)
    with open(config_file) as file:
        config_full = yaml.load(file)

    # write the run configuration to the log file
    with open(log_file, 'a') as file:
        file.write("\n\n### CONFIGURATION ###\n")
        documents = yaml.dump(config_full,file, default_flow_style=False)
        file.write("### END CONFIGURATION ###\n")


    return True
