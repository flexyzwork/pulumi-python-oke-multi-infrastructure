import pulumi_oci as oci

from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger
from utils.resource_helper import create_resource

logger = global_logger


@apply_exception_handler
class CompartmentManager:
    def __init__(self, region, config):
        self.region = region
        self.config = config

    def create_compartment(self):
        """Compartment 생성"""
        return create_resource(
            oci.identity.Compartment,
            self.config.provider,
            self.region,
            self.config.tenancy,  # 최상위 compartment_id
            None,
            name=f'oke-{self.region}',  # Compartment 생성에 필요한 인수
            description='An compartment created by Pulumi',
        )
