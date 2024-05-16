from google.cloud import compute_v1
# from google.cloud.utils import wait_for_extended_operation
import time

def wait_for_extended_operation(operation, operation_type):
    """Waits for a long-running operation to complete."""
    print(f"Waiting for {operation_type}...")
    while True:
        result = operation.result()
        print(result)
        if result.status == "DONE":
            print(f"{operation_type} completed.")
            if result.error:
                raise Exception(result.error.message)
            return result
        time.sleep(1)

def create_network(project_id, network_name):
    """Creates a VPC network."""
    client = compute_v1.NetworksClient()
    network = compute_v1.Network()
    network.name = network_name
    # Disable automatic subnet creation
    network.auto_create_subnetworks = False
    operation = client.insert(project=project_id, network_resource=network)
    # wait_for_extended_operation(operation, "network creation")
    time.sleep(60)

    return network

def create_subnet(project_id, region, subnet_name, network_name, ip_cidr_range):
    """Creates a subnet within a VPC network."""
    client = compute_v1.SubnetworksClient()
    subnet = compute_v1.Subnetwork()
    subnet.name = subnet_name
    subnet.ip_cidr_range = ip_cidr_range
    subnet.network = f"projects/{project_id}/global/networks/{network_name}"
    subnet.region = region
    operation = client.insert(project=project_id, region=region, subnetwork_resource=subnet)
    # wait_for_extended_operation(operation, "subnet creation")
    return subnet

project_id = "blank-test-419906"
network_name = "your-network-name"
region = "us-central1"
subnet_name = "your-subnet-name"
ip_cidr_range = "10.1.2.0/24"

network = create_network(project_id, network_name)
create_subnet(project_id, region, subnet_name, network_name, ip_cidr_range)
