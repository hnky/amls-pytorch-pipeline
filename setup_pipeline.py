import azureml
from azureml.core import VERSION
from azureml.core import Workspace, Experiment, Datastore, Environment
from azureml.core.runconfig import RunConfiguration
from azureml.data.datapath import DataPath, DataPathComputeBinding
from azureml.data.data_reference import DataReference
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.pipeline.core import Pipeline, PipelineData, PipelineParameter
from azureml.pipeline.steps import PythonScriptStep, EstimatorStep
from azureml.train.estimator import Estimator
from azureml.train.dnn import PyTorch
import sys, getopt, os

## Get arguments
def printhelp():
        print ('Arguments:')
        print ('  -c    Compute Target name')
        print ('  -m    Model name')
        print ('  -e    Experiment name')

experiment_name = 'Simpsons-PT-Pipeline-DevOps'
compute_target = 'OptimusPrime'
script_folder = "./scripts"
model_name = "Simpsons-PT-DevOps"

try:
    print('Arguments: ', sys.argv[1:])
    opts, args = getopt.getopt(sys.argv[1:],"d:p:c:v:s:a:k:r:w:")
except getopt.GetoptError:
    printhelp
for opt, arg in opts:
    if opt == '-h':
        printhelp
    elif opt == '-c':
        compute_target = arg
    elif opt == '-m':
        model_name = arg
    elif opt == '-e':
        experiment_name = arg

print("Azure ML SDK Version: ", VERSION)

#### Connect to our environment ####
##################################

# Connect to workspace
ws = Workspace.from_config()
print("Workspace:",ws.name,"in region", ws.location)

# Connect to compute cluster
cluster = ComputeTarget(workspace=ws, name=compute_target)
print('Compute cluster:', cluster.name)

# Connect to the default datastore
ds = ws.get_default_datastore()
print("Datastore:",ds.name)

# Connect to the experiment
experiment = Experiment(workspace=ws, name=experiment_name)
print("Experiment:",experiment.name)


#### Define Pipeline! ####
##########################

# The following will be created and then run:
# 1. Pipeline Parameters
# 2. Data Process Step
# 3. Training Step
# 4. Model Registration Step
# 5. Pipeline registration
# 6. Submit the pipeline for execution


## Pipeline Parameters ##
# We need to tell the Pipeline what it needs to learn to see!

source_dataset = DataPath(
    datastore=ds, 
    path_on_datastore="simpsonslego-v3")

source_dataset_param = (PipelineParameter(name="source_dataset",default_value=source_dataset),
                          DataPathComputeBinding())

# Configuration for data prep and training steps #

## Data Process Step ##
# prep.py file versions our data in our data source #

# Output location for the pre-proccessed trainings images
training_data_location = PipelineData(name="simpsons_training_data", datastore=ds)

# Create the pre-process step
preProcessDataStep = PythonScriptStep(
    name="Pre-process data",
    script_name="steps/prep.py",
    compute_target=cluster,
    inputs=[source_dataset_param],
    arguments=['--source_path', source_dataset_param,
                '--destination_path', training_data_location
                ],
    outputs=[training_data_location],
    source_directory=script_folder)

## Training Step ##
# train.py does the training based on the processed data #
# Output location for the produced model
model = PipelineData(name="model", datastore=ds, output_path_on_compute="model")

# Estimator script params
estimator_script_params = [
    "--data-folder", training_data_location,
    "--output-folder", model
]

# Create the tensorflow Estimator
trainEstimator = PyTorch(
    source_directory = script_folder,
    compute_target = cluster,
    entry_script = "steps/train.py", 
    use_gpu = True,
    framework_version='1.3'
)

# Create a pipeline step with the TensorFlow Estimator
trainOnGpuStep = EstimatorStep(
    name='Train Estimator Step',
    estimator=trainEstimator,
    inputs=[training_data_location],
    outputs=[model],
    compute_target=cluster,
    estimator_entry_script_arguments = estimator_script_params
) 

## Register Model Step ##
# Once training is complete, register.py registers the model with AML #

# Configuration for registration step #
registerModelStep = PythonScriptStep(
    name="Register model in Model Management",
    script_name="steps/register.py",
    compute_target=cluster,
    inputs=[model],
    arguments=['--model_name', model_name,
                '--model_assets_path', model
                ],
    source_directory=script_folder
)

## Create and publish the Pipeline ##
# We now define and publish the pipeline #

pipeline = Pipeline(workspace=ws, steps=[preProcessDataStep,trainOnGpuStep,registerModelStep])

published_pipeline = pipeline.publish(
    name="Simpsons-PyTorch-Pipeline - Training pipeline (From DevOps)", 
    description="Training pipeline (From Azure DevOps)")

## Submit the pipeline to be run ##
# Finally, we submit the pipeline for execution #

pipeline_run = published_pipeline.submit(ws,experiment_name)
print('Run created with ID: ', pipeline_run.id)