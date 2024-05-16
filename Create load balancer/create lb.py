from google.cloud import compute_v1
from google.api_core.extended_operation import ExtendedOperation
from google.api_core import exceptions as core_exceptions  # Import the exceptions module

def wait_for_extended_operation(
    operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 300
) -> any:
    """
    Waits for the extended (long-running) operation to complete.

    If the operation is successful, it will return its result.
    If the operation ends with an error, an exception will be raised.
    If there were any warnings during the execution of the operation
    they will be printed to sys.stderr.

    Args:
        operation: a long-running operation you want to wait on.
        verbose_name: (optional) a more verbose name of the operation,
            used only during error and warning reporting.
        timeout: how long (in seconds) to wait for operation to finish.
            If None, wait indefinitely.

    Returns:
        Whatever the operation.result() returns.

    Raises:
        This method will raise the exception received from `operation.exception()`
        or RuntimeError if there is no exception set, but there is an `error_code`
        set for the `operation`.

        In case of an operation taking longer than `timeout` seconds to complete,
        a `concurrent.futures.TimeoutError` will be raised.
    """
    result = operation.result(timeout=timeout)

    if operation.error_code:
        print(
            f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}",
            file=sys.stderr,
            flush=True,
        )
        print(f"Operation ID: {operation.name}", file=sys.stderr, flush=True)
        raise operation.exception() or RuntimeError(operation.error_message)

    if operation.warnings:
        print(f"Warnings during {verbose_name}:\n", file=sys.stderr, flush=True)
        for warning in operation.warnings:
            print(f" - {warning.code}: {warning.message}", file=sys.stderr, flush=True)

    return result


def create_firewall_rule(project_id, network_name):
    """Creates a firewall rule to allow traffic to the load balancer."""
    print("pass firewall_rule create")
    # client = compute_v1.FirewallsClient()
    # firewall_rule = compute_v1.types.compute.Firewall()
    # firewall_rule.name = "allow-lb-traffic"
    # firewall_rule.direction = "INGRESS"
    # firewall_rule.network = f"projects/{project_id}/global/networks/{network_name}"
    # firewall_rule.allowed = [
    #     compute_v1.Allowed(
    #         I_p_protocol="tcp",
    #         ports=["80"]  # Adjust port as needed
    #     )
    # ]
    # firewall_rule.source_ranges = ["0.0.0.0/0"]  # Allow traffic from anywhere
    # operation = client.insert(project=project_id, firewall_resource=firewall_rule)
    # wait_for_extended_operation(operation, "firewall creation")

def create_health_check(project_id):
    """Creates a health check for the backend service."""
    print("pass health_check create")
    
    client = compute_v1.HealthChecksClient()
    health_check = compute_v1.HealthCheck()
    health_check.name = f"basic-check{n}"
    health_check.type_ = "HTTP"
    health_check.http_health_check = compute_v1.HTTPHealthCheck(
        port_specification="USE_SERVING_PORT"
    )
    operation = client.insert(project=project_id, health_check_resource=health_check)
    wait_for_extended_operation(operation, "health check creation")

    if not health_check.self_link:  # Check if selfLink is empty
        health_check = client.get(project=project_id, health_check=health_check.name)
    return health_check

def create_backend_service(project_id, health_check):
    """Creates a backend service with instance groups."""
    client = compute_v1.BackendServicesClient()
    backend_service = compute_v1.BackendService()
    backend_service.name = f"backend-service{n}"
    backend_service.load_balancing_scheme = "EXTERNAL"
    backend_service.protocol = "HTTP"
    backend_service.health_checks = [health_check.self_link]
    # Add backend instance groups here...
    operation = client.insert(project=project_id, backend_service_resource=backend_service)
    wait_for_extended_operation(operation, "backend service creation")
    if not backend_service.self_link:  # Check if selfLink is empty
        backend_service = client.get(project=project_id, backend_service=backend_service.name)


    backend_service = client.get(project=project_id, backend_service=backend_service.name)

    print("adding components in backends")

    return backend_service


# def create_instance_group(
#     project_id: str,
#     zone: str,
#     group_name: str,
#     instance_template_name: str,
#     backend_service,
#     size: int = 1,  # Default size
# ):
#     """Creates an instance group in the specified zone."""
    
#     # Create compute client
#     client = compute_v1.InstanceGroupsClient()

#     # Construct the request body for creating the instance group.
#     instance_group_resource = compute_v1.InstanceGroup()
#     instance_group_resource.name = group_name
    
#     # Set the URL for the instance template that the instance group will use.
#     instance_group_resource.instance_template_resources = f"projects/{project_id}/global/instanceTemplates/{instance_template_name}"
    
#     # Create the instance group.
#     request = compute_v1.CreateInstanceGroupRequest()
#     request.project = project_id
#     request.zone = zone
#     request.instance_group_resource = instance_group_resource
    
#     # Execute the request to create the instance group
#     operation = client.create_instance_group(request)
    
#     # Print the operation result
#     print(f"Instance Group creation operation: {operation.name}")

#     # Update backends
#     backend_service.backends = [
#     compute_v1.Backend(
#         group=f"projects/{project_id}/zones/{zone}/instanceGroups/{group_name}"
#     ) 
#     ]

#     operation = client.update(project=project_id, backend_service_resource=backend_service.self_link)
#     wait_for_extended_operation(operation, "backend service update")

#     return backend_service

def create_instance_template(project_id, template_name, machine_type="e2-micro", 
                             source_image_family="debian-11", source_image_project="debian-cloud"):
    """Creates an instance template with specified parameters."""
    
    config = compute_v1.InstanceProperties()
    # Set up the machine type
    config.machine_type = machine_type
    
    # Describe the boot disk and the image to use as a source.
    config.disks = [compute_v1.AttachedDisk(
        auto_delete=True,
        boot=True,
        initialize_params=compute_v1.AttachedDiskInitializeParams(
            source_image=f"projects/{source_image_project}/global/images/family/{source_image_family}",
        ),
    )]
    # Use the network interface provided in the network_interface argument
    config.network_interfaces = [compute_v1.NetworkInterface(
        name=f"interface{n}",
        subnetwork = "https://www.googleapis.com/compute/v1/projects/blank-test-419906/regions/us-central1/subnetworks/your-subnet-name",
        network = "https://www.googleapis.com/compute/v1/projects/blank-test-419906/global/networks/your-network-name",
        # access_configs=[
        #     compute_v1.AccessConfig(name="nat_i_p",
        #     network_tier="PREMIUM",
        #     )
        # ]
    )]

    # Create the instance template resource
    template = compute_v1.InstanceTemplate()
    template.name = template_name+str(n)
    template.properties = config

    template_client = compute_v1.InstanceTemplatesClient()
    
    operation = template_client.insert(
        project=project_id, instance_template_resource=template
    )
    # .... rest of the code ...
    # except core_exceptions.HttpException as e:  # Correctly catch the exception type
    #     print(f"Error creating instance template: {e.message}")
    #     raise  # Re-raise the exception to propagate the error

    # wait_for_extended_operation(operation, "instance template creation")
    return template

def create_instance_group(project_id, zone, instance_group_name,backend_service, template_url, size=1, port_name="http", port=80):
    """Creates an instance group with specified parameters."""
    
    # Define instance template
    instance_template_cache = compute_v1.InstanceTemplate()
    instance_template_cache.name = instance_group_name + "-template"  # Ensure unique template name
    instance_template_cache.source_instance = template_url.self_link   

    # Create instance group
    client = compute_v1.InstanceGroupManagersClient()
    instance_group = compute_v1.InstanceGroupManager()
    instance_group.name = instance_group_name
    instance_group.named_ports = [compute_v1.NamedPort(name=port_name, port=port)]  # Define named port
    instance_group.instance_template = instance_template_cache.self_link  
    instance_group.target_size = 2
    print(instance_template_cache.self_link)
    print(template_url)
    print(template_url.self_link)
    # Adjust for regional/zonal groups (optional)
    # If regional, set: instance_group.region = region  
    # request = compute_v1.InsertInstanceGroupRequest(project=project_id, zone=zone, instance_group_resource=instance_group)

    operation = client.insert(project=project_id, zone=zone, instance_group_manager_resource=instance_group)
    wait_for_extended_operation(operation, "instance group creation")

    #     # Update backends
#     backend_service.backends = [
#     compute_v1.Backend(
#         group=f"projects/{project_id}/zones/{zone}/instanceGroups/{group_name}"
#     ) 
#     ]

#     operation = client.update(project=project_id, backend_service_resource=backend_service.self_link)
#     wait_for_extended_operation(operation, "backend service update")

#     return backend_service

    return instance_group




def create_url_map(project_id, backend_service):
    """Creates a URL map to route requests to the backend service."""
    client = compute_v1.UrlMapsClient()
    url_map = compute_v1.UrlMap()
    url_map.name = f"url-map{n}"
    url_map.default_service = backend_service.self_link


    operation = client.insert(project=project_id, url_map_resource=url_map)
    wait_for_extended_operation(operation, "url map creation")
    return url_map

def create_global_forwarding_rule(project_id, url_map):
    """Creates a global forwarding rule to direct traffic to the URL map."""
    client = compute_v1.GlobalForwardingRulesClient()
    forwarding_rule = compute_v1.ForwardingRule()
    forwarding_rule.name = "forwarding-rule"
    forwarding_rule.load_balancing_scheme = "EXTERNAL"
    forwarding_rule.port_range = "80"
    forwarding_rule.I_p_protocol = "TCP"
    forwarding_rule.target = url_map.self_link
    operation = client.insert(project=project_id, forwarding_rule_resource=forwarding_rule)
    wait_for_extended_operation(operation, "forwarding rule creation")
    backend_service.backends = [
    compute_v1.Backend(
        group=f"projects/{project_id}/zones/{zone}/instanceGroups/{instance_group_name}"
    ) 
    # Add more backends as needed...
]

# operation = client.update(project=project_id, backend_service=backend_service)
# wait_for_extended_operation(operation, "backend service update")

# Replace with your project ID and network name
project_id = "blank-test-419906"
network_name = "your-network-name"
region = "us-central1"
instance_group_name = "name"
zone = "us-central1-a"
group_name = "your-group-name"
instance_template_name = "your-instance-name-template"
n = 31
# Create firewall rule
print("creating firewall_rule")
create_firewall_rule(project_id, network_name)

print("creating health check")

# Create health check
health_check = create_health_check(project_id)
# Create backend service and add instance groups (replace placeholders)

print("creating backend_service")
print("skip backend creation for now")
backend_service = create_backend_service(project_id, health_check) 

print("creating instance group")

template = create_instance_template(project_id,instance_template_name)




backend_service = create_instance_group(
    project_id,
    zone,
    instance_template_name,
    backend_service,
    template_url = template,
      # Default size
)



print("creating URL map")
# Create URL map
url_map = create_url_map(project_id, backend_service)

print("creating global forwarding rule")

# Create global forwarding rule 
create_global_forwarding_rule(project_id, url_map)
