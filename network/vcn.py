import pulumi_oci as oci

from utils.resource_helper import create_resource


class VCNManager:
    def __init__(self, region, config, compartment_id):
        self.region = region
        self.config = config
        self.compartment_id = compartment_id

    def create_vcn(self):
        """VCN 생성"""
        return create_resource(
            oci.core.Vcn,
            self.config.provider,
            self.region,
            self.compartment_id,
            None,
            dns_label=f'{self.region}vcn',
            cidr_block=self.config.vcn_cidr_block,
        )
