import pulumi_oci as oci

from config import RouteTableIDs
from utils.resource_helper import create_resource


class RouteTableManager:
    """
    라우트 테이블 생성 및 관리 클래스
    """

    def __init__(self, region, config, compartment_id, vcn_id, gateway_ids, regions, peers):
        self.region = region
        self.config = config
        self.compartment_id = compartment_id
        self.vcn_id = vcn_id
        self.gateway_ids = gateway_ids
        self.regions = regions
        self.peers = peers
        self.route_table_ids = RouteTableIDs()

    def create_route_table_private(self):
        """
        프라이빗 라우트 테이블 생성 메소드
        """
        route_rules = [
            oci.core.RouteTableRouteRuleArgs(
                description='traffic to the internet',
                destination='0.0.0.0/0',
                destination_type='CIDR_BLOCK',
                network_entity_id=self.gateway_ids.nat_gateway_id,
            ),
            oci.core.RouteTableRouteRuleArgs(
                description='traffic to OCI services',
                destination=self.config.service_cidr,
                destination_type='SERVICE_CIDR_BLOCK',
                network_entity_id=self.gateway_ids.service_gateway_id,
            ),
        ]
        if self.peers and self.gateway_ids.dynamic_routing_gateway_id:
            for peer in self.peers:
                peer_route_rule = [
                    oci.core.RouteTableRouteRuleArgs(
                        description=f'{str(peer).upper()}로의 트래픽',
                        destination=self.regions[peer].vcn_cidr_block,
                        destination_type='CIDR_BLOCK',
                        network_entity_id=self.gateway_ids.dynamic_routing_gateway_id,
                    )
                ]
                route_rules.extend(peer_route_rule)

        return create_resource(
            oci.core.RouteTable,
            self.config.provider,
            self.region,
            self.compartment_id,
            'private',
            vcn_id=self.vcn_id,
            route_rules=route_rules,
        )

    def create_route_table_public(self):
        """
        퍼블릭 라우트 테이블 생성 메소드
        """
        route_rules = [
            oci.core.RouteTableRouteRuleArgs(
                description='traffic to/from internet',
                destination='0.0.0.0/0',
                destination_type='CIDR_BLOCK',
                network_entity_id=self.gateway_ids.internet_gateway_id,
            )
        ]

        return create_resource(
            oci.core.RouteTable,
            self.config.provider,
            self.region,
            self.compartment_id,
            'public',
            vcn_id=self.vcn_id,
            route_rules=route_rules,
        )

    def create_route_tables(self):
        """
        모든 라우트 테이블을 생성하는 메소드
        """
        self.route_table_ids.route_table_private_id = self.create_route_table_private()
        self.route_table_ids.route_table_public_id = self.create_route_table_public()

        return self.route_table_ids
