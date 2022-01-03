"""
usage: import_acr.py [-h] -w WORKSPACE -a CONTAINER_REGISTRY -wsg WS_RESOURCE_GROUP -crg CR_RESOURCE_GROUP -s SUBSCRIPTION

Import Azure ML compute runtime images to the specified Container Registry from the ML workspace global registry

optional arguments:
  -h, --help            show this help message and exit
  -w WORKSPACE, --workspace WORKSPACE
                        Name of the ML Workspace
  -a CONTAINER_REGISTRY, --container-registry CONTAINER_REGISTRY
                        Name of the Container Registry
  -wsg WS_RESOURCE_GROUP, --ws-resource-group WS_RESOURCE_GROUP
                        Name of resource group of the ML Workspace
  -crg CR_RESOURCE_GROUP, --cr-resource-group CR_RESOURCE_GROUP
                        Name of resource group of the Container Registry
  -s SUBSCRIPTION, --subscription SUBSCRIPTION
                        ID of subscription that the ML Workspace and Container Registry are in
--------
example:
> conda create -n dlp -y python=3.7
> conda activate dlp
> pip install azureml-core~=1.37 azure-cli~=2.18
> az login
> az acr login -n myregistry
> python import_acr.py -w myworkspace -a myregistry -wsg myrg -crg myrg -s 12345678-0000-0000-0000-abcd12345678
"""

import argparse
import sys
from azure.cli.core import get_default_cli
from azureml.core import Workspace, Environment


def get_viennaglobal_registry(workspace_name: str, resource_group: str, subscription_id: str):
    ws = Workspace(subscription_id, resource_group, workspace_name)
    env = Environment(name='AzureML-sklearn-0.24-ubuntu18.04-py37-cpu')
    registry = dict(env.get_image_details(ws))['dockerImage']['registry']
    return (registry['address'], registry['username'], registry['password'], ws.location)


def az_acr_import(src_img: str, src_addr: str, src_user: str, src_pwd: str, dest_img: str, dest_acr: str, dest_rg: str, dest_sub: str):
    try:
        args = [
            'acr', 'import',
            '--source', f'{src_addr}/{src_img}',
            '--username', src_user,
            '--password', src_pwd,
            '--image', dest_img,
            '--name', dest_acr,
            '--resource-group', dest_rg,
            '--subscription', dest_sub,
            '--force',
        ]
        print(f'Invoking Az CLI:\naz {" ".join(args)}')
        cli = get_default_cli()
        return cli.invoke(args)
    except Exception as e:
        print(f'Az CLI returned error: {e}.')
        return -1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Import Azure ML compute runtime images to the specified Container Registry from the ML workspace global registry')
    parser.add_argument('-w', '--workspace', type=str, required=True,
                        help='Name of the ML Workspace')
    parser.add_argument('-a', '--container-registry', type=str, required=True,
                        help='Name of the Container Registry')
    parser.add_argument('-wsg', '--ws-resource-group', type=str, required=True,
                        help='Name of resource group of the ML Workspace')
    parser.add_argument('-crg', '--cr-resource-group', type=str, required=True,
                        help='Name of resource group of the Container Registry')
    parser.add_argument('-s', '--subscription', type=str, required=True,
                        help='ID of subscription that the ML Workspace and Container Registry are in')
    args = parser.parse_args()

    print('Resolving viennaglobal registry...')
    src_addr, src_user, src_pwd, region = get_viennaglobal_registry(
        args.workspace, args.ws_resource_group, args.subscription)

    print(f'Resolved registry detail, address: {src_addr}, region: {region}')
    print('Starting to import images...')

    for repo in [
        'boot/vm-bootstrapper/binimage/linux',
        'exe/execution-wrapper/installed',
        'cap/lifecycler/installed',
        'cap/cs-capability/installed',
        'cap/data-capability/installed',
        'cap/hosttools-capability/installed',
    ]:
        if az_acr_import(f'{repo}:{region}-stable', src_addr, src_user, src_pwd,
                         f'{repo}:stable',
                         args.container_registry,
                         args.cr_resource_group,
                         args.subscription) != 0:
            print('Failed to import image. Please see error details above.')
            sys.exit(1)

    print('Successfully imported image')
    print(
        f'Submit run with this environment variable:\n\nAZUREML_CR_BOOTSTRAPPER_CONFIG_OVERRIDE=\'{{"capabilities_registry": {{"registry": {{"url": "{args.container_registry}.azurecr.io", "username": "<USER_NAME>", "password": "<PASSWORD>"}}, "regional_tag_prefix": false}}}}\'')
