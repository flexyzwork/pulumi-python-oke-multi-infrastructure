import pulumi
import pulumi_oci as oci

from utils.logger import global_logger

logger = global_logger


class PublicIpManager:
    def __init__(self, region, config, compartment_id):
        self.region = region
        self.config = config
        self.compartment_id = compartment_id

    def reserve_public_ip(self):
        """Compartment에서 Public IP 예약"""
        public_ip = oci.core.PublicIp(
            f'{self.region}-public-ip',
            compartment_id=self.compartment_id,
            display_name='nlb-ip',
            lifetime='RESERVED',
            opts=pulumi.ResourceOptions(provider=self.config.provider),
        )

        public_ip.ip_address.apply(lambda public_ip: public_ip)
        pulumi.export(f'{self.region}-public_ip_address', public_ip.ip_address)
        public_ip.ip_address.apply(lambda ip_value: logger.info(f'public_ip_address created with ID: {ip_value}'))
