# Azure Machine Learning Data Loss Prevention (Private Preview)

## Enable Your Subscription for Private Preview
Submit [this form](https://forms.office.com/r/1TraBek7LV) to allowlist your subscription(s).

## What is Data Loss Prevention (DLP)?

AzureML has an outbound dependency to storage.reigon/*.blob.core.windows.net. This configuration increases the risk of allowing malicious users to move the data from your virtual network to other storage accounts in the same region.

## What is supported, What is not supported in Private Preview

With this private preview, we can support DLP with training and inferencing. However, all scenarios are not supported, which use Vienna Global ACR.

|Scenarios|Status
|---|---|
|1. Training Experience using Python SDK on Compute Instance, Compute Cluster, Integrated Notebook on UX|Supported with the workaround described below|---|
|2. Inferencing Experience using AKS, ArcAKS| Supported w/o workaround |
|3. AutoML UX, Designer UX, Cureated Environment use Vienna Global ACR (ACR managed by Microsoft) | Not Supported|

## Workaround for the Training Experience (#1)

At first, do not forget to submit [this form](https://forms.office.com/r/1TraBek7LV). We need to allowlist your subscription(s), which will take a week.

### Inbound Configurations
* Allow the inbound from service tag "Azure Machine Learning"
* If you use a firewall, you need to configure UDR to make inbound communication skip your firewall. See [this doc](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-secure-training-vnet?tabs=azure-studio%2Cipaddress#inbound-traffic).

Note that the inbound from service tag "Batch node management" is not required anymore.

### Outbound Configurations

#### NSG Case
* Destination port 443 over TCP to BatchNodeManagement.region 
* Destination port 443 over TCP to Storage.region (Service Endpoint Policy will narrow it down in the later step.) 

#### FW Case
* Destination port 443 to region.batch.azure.com, region.service.batch.com.
* Destination port 443 over TCP to *.blob.core.windows.net (SEP will narrow it down in the later step.)

### Service Endpoint Policy Configuration

We use [service endpoint policy](https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-service-endpoint-policies-overview) to narrow down the target storage accounts of the outbound to storage.region/*.blob.core.windows.net.

* Enable the storage service endpoint of your subnet has your compute
* Create a service endpoint policy with **/services/Azure/MachineLearning** alias.
* Attach your service endpoint policy to your subnet has your compute.

If you do not have storage private endpoints for Azure Machine Learning Vnet, you need to do the following.
* Add your storage accounts in your service endpoint policy that you want to allow access from your compute. At least, you need to add the default storage account attached to your AzureML workspace.

### Run the script to copy the system images from Vienna Global ACR to your ACR attached to AzureML

You need to copy the system images to your ACR not to use Vienna Global ACR and use these copied images for training job submission. Note that this is for the AzureML internal job submission process, and you need to have your docker images to build your environment for your training.

* Run [this script](import_acr.py) and make copies of system images to your ACR.
  * pip install azureml-core~=1.37 azure-cli~=2.18
  * az login
  * az acr login -n myregistry
  * python import_acr.py -w myworkspace -a myregistry -wsg myrg -crg myrg -s mysubscriptionid
* Add below two lines when you submit your training job.
  * myenv.environment_variables['AZUREML_COMPUTE_USE_COMMON_RUNTIME'] = 'true'
  * myenv.environment_variables['AZUREML_CR_BOOTSTRAPPER_CONFIG_OVERRIDE'] = "{\"capabilities_registry\": {\"registry\": {\"url\": \"<<user acr name>>.azurecr.io\", \"username\": \"<<ACR Admin Username>>\", \"password\": \"<<ACR Admin Key>>\"},\"regional_tag_prefix\": false}}"
    * Note that you need to replace ACR name, Admin Username and Admin Key.

### Prepare your images in your ACR for training/inferencing

You need to prepare your images for training and inferencing because our Vienna Global ACR does not support DLP. See [this doc](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-train-with-custom-image).

## Frequently Asked Questions
To be updated.
