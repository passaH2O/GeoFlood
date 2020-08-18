import configparser
import os
import sys
import inspect

def cfg_finder():
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_pointer_fn = os.path.join(current_dir,"GeoNet","project_pointer.cfg")
    config_point = configparser.ConfigParser()
    config_point.read(cfg_pointer_fn)
    main_cfg = config_point.get('CFG Directory','project_cfg_pointer')
    print(f'Using configuration settings here: {main_cfg}')
    config = configparser.ConfigParser()
    config.read(main_cfg)
    geofloodHomeDir = config.get('Section', 'geofloodhomedir')
    projectName = config.get('Section', 'projectname')
    DEM_name = config.get('Section', 'dem_name')
    chunk_status = int(config.get('Section', 'Chunk_DEM'))
    input_fn = config.get('Section','Input_dir')
    output_fn = config.get('Section','Output_dir')
    hr_status = int(config.get('Section','hr_flowline'))
    return geofloodHomeDir,projectName,DEM_name,chunk_status,input_fn,output_fn,hr_status
