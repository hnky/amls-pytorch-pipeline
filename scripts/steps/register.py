from azureml.core import Workspace
from azureml.core.model import Model
from azureml.core import Run
import argparse
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        '--model_name', type=str, default='',help='Name you want to give to the model.'
    )
    
    parser.add_argument(
        '--model_assets_path',type=str, default='outputs',help='Location of trained model.'
    )

    args,unparsed = parser.parse_known_args()
    
    print('Model assets path is:',args.model_assets_path)
    print('Model name is:',args.model_name)
      
    run = Run.get_context()
   
    pipeline_run = Run(run.experiment, run._root_run_id)
    pipeline_run.upload_file("outputs/model/model.pth",os.path.join(args.model_assets_path,"model.pth"))
    pipeline_run.upload_file("outputs/model/labels.txt",os.path.join(args.model_assets_path,"labels.txt"))
    pipeline_run.upload_file("outputs/deployment/score.py","deployment/score.py")
    pipeline_run.upload_file("outputs/deployment/myenv.yml","deployment/myenv.yml")
    pipeline_run.upload_file("outputs/deployment/inferenceconfig.json","deployment/inferenceconfig.json")
    pipeline_run.upload_file("outputs/deployment/deploymentconfig_aci.json","deployment/deploymentconfig_aci.json")
    pipeline_run.upload_file("outputs/deployment/deploymentconfig_aks.json","deployment/deploymentconfig_aks.json")

    tags = {
       "Conference":"Demo"
    }

    model = pipeline_run.register_model(model_name=args.model_name, model_path='outputs/',tags=tags)
       
    print('Model registered: {} \nModel Description: {} \nModel Version: {}'.format(model.name, model.description, model.version))