import pulumi
import pulumi_oci as oci

from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger

logger = global_logger


@apply_exception_handler
def create_resource(
    resource_type: type[pulumi.CustomResource],
    provider: oci.Provider,
    region: str,
    compartment_id: str | None = None,
    suffix: str | None = None,
    **kwargs,
) -> pulumi.Output:
    """
    리소스를 생성하고 로깅 및 ID를 익스포트하는 유틸리티 함수.

    Args:
        resource_type (Type[pulumi.CustomResource]): 생성할 리소스 클래스 (예: oci.identity.Compartment).
        provider (oci.Provider): OCI provider 객체.
        region (str): 리소스가 생성될 지역 이름.
        compartment_id (Optional[str], optional): 리소스가 속할 compartment의 OCID.
        suffix (Optional[str], optional): 리소스 이름에 추가할 접미사.
        **kwargs: 리소스 생성에 필요한 추가 매개변수.

    Returns:
        pulumi.Output: 생성된 리소스의 ID를 반환하는 Pulumi Output 객체.
    """
    try:
        # Validate resource_type
        if not issubclass(resource_type, pulumi.CustomResource):
            raise ValueError(f'Invalid resource type: {resource_type}. Must be a subclass of pulumi.CustomResource.')

        # Construct resource name
        resource_name = f'{region}-{resource_type.__name__.lower()}'
        if suffix:
            resource_name = f'{resource_name}-{suffix}'

        logger.info(f'Creating {resource_type.__name__} in region: {region.upper()}')

        # Set compartment_id if provided
        if compartment_id:
            kwargs['compartment_id'] = compartment_id

        # Set display_name for network-related resources
        network_resource_types = [
            oci.core.Vcn,
            oci.core.Subnet,
            oci.core.InternetGateway,
            oci.core.RouteTable,
            oci.core.SecurityList,
            oci.core.Drg,
            oci.core.NatGateway,
            oci.core.ServiceGateway,
            oci.core.RemotePeeringConnection,
        ]
        if resource_type in network_resource_types and 'display_name' not in kwargs:
            kwargs['display_name'] = resource_name

        opts = pulumi.ResourceOptions(provider=provider)
        if 'opts' in kwargs:
            opts = pulumi.ResourceOptions.merge(kwargs['opts'], opts)
            del kwargs['opts']

        # Create the resource
        resource = resource_type(resource_name, opts=opts, **kwargs)

        # Export the resource ID and log the creation
        pulumi.export(f'{resource_name}_id', resource.id)
        resource.id.apply(lambda id_value: logger.info(f'{resource_type.__name__} created with ID: {id_value}'))

        return resource.id

    except Exception as e:
        logger.error(f'Failed to create resource {resource_type.__name__} in region {region.upper()}: {e}')
        raise
