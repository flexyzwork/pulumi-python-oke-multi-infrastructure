import pulumi_oci as oci

from config import GatewayIDs
from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger
from utils.resource_helper import create_resource

logger = global_logger


@apply_exception_handler
class GatewayManager:
    def __init__(self, region, config, compartment_id, vcn_id, peers=None):
        self.region = region
        self.config = config
        self.compartment_id = compartment_id
        self.vcn_id = vcn_id
        self.peers = peers
        self.gateway_ids = GatewayIDs()

    def create_internet_gateway(self):
        """인터넷 게이트웨이 생성 및 할당"""
        return create_resource(
            oci.core.InternetGateway,
            self.config.provider,
            self.region,
            self.compartment_id,
            None,
            vcn_id=self.vcn_id,
            enabled=True,
        )

    def create_nat_gateway(self):
        """NAT 게이트웨이 생성 및 할당"""
        return create_resource(
            oci.core.NatGateway,
            self.config.provider,
            self.region,
            self.compartment_id,
            None,
            vcn_id=self.vcn_id,
        )

    def create_service_gateway(self):
        """서비스 게이트웨이 생성 및 할당"""
        return create_resource(
            oci.core.ServiceGateway,
            self.config.provider,
            self.region,
            self.compartment_id,
            None,
            vcn_id=self.vcn_id,
            services=[oci.core.ServiceGatewayServiceArgs(service_id=self.config.service_id)],
        )

    def create_dynamic_routing_gateway(self):
        """DRG 생성"""
        return create_resource(
            oci.core.Drg,
            self.config.provider,
            self.region,
            self.compartment_id,
            None,
        )

    def attach_drg_to_vcn(self):
        """DRG를 VCN에 연결"""
        return create_resource(
            oci.core.DrgAttachment,
            self.config.provider,
            self.region,
            None,
            None,
            vcn_id=self.vcn_id,
            drg_id=self.gateway_ids.dynamic_routing_gateway_id,
            remove_export_drg_route_distribution_trigger=True,
        )

    def create_gateways(self):
        """모든 게이트웨이 생성 및 반환"""
        self.gateway_ids.internet_gateway_id = self.create_internet_gateway()
        self.gateway_ids.nat_gateway_id = self.create_nat_gateway()
        self.gateway_ids.service_gateway_id = self.create_service_gateway()

        if self.peers:
            self.gateway_ids.dynamic_routing_gateway_id = self.create_dynamic_routing_gateway()
            self.attach_drg_to_vcn()
        return self.gateway_ids
