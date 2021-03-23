from azureml.core import Workspace
from azureml.core import Run
from azureml.core import Experiment
import argparse
import json
import os
import glob
from distutils.dir_util import copy_tree

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--source_path',
        type=str,
        default='',
        help='Path of the source data'
    )
    parser.add_argument(
        '--destination_path',
        type=str,
        default='',
        help='Path of the processed data'
    )

    args,unparsed = parser.parse_known_args()
    print('Source Path '+ args.source_path)
    print('Destination Path '+ args.destination_path)

    run = Run.get_context()
    pipeline_run_Id = run._root_run_id
   
    print("Pipeline Run Id: ",pipeline_run_Id)

    # Create the output folder
    os.makedirs(args.destination_path, exist_ok=True)
       
    copy_tree(args.source_path, args.destination_path)
    
    print("Done: ",pipeline_run_Id)