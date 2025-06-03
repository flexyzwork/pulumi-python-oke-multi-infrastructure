from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger

from .gateway import GatewayManager
from .remote_peering_connection import RemotePeeringConnectionManager
from .routing import RouteTableManager
from .security import SecurityListManager
from .subnet import SubnetManager
from .vcn import VCNManager

logger = global_logger


@apply_exception_handler
class NetworkManager:
    def __init__(self, region, config, compartment_id, regions, peers=None):
        self.region = region
        self.config = config
        self.compartment_id = compartment_id
        self.peers = peers
        self.regions = regions

    def create_network(self):
        # Step 1: VCN 생성
        vcn_manager = VCNManager(self.region, self.config, self.compartment_id)
        vcn_id = vcn_manager.create_vcn()

        # Step 2: 게이트웨이 생성 (인터넷, NAT, 서비스, 동적라우팅)
        gateway_manager = GatewayManager(self.region, self.config, self.compartment_id, vcn_id, self.peers)
        gateway_ids = gateway_manager.create_gateways()

        remote_peering_connection_ids = {}
        #  Step 2.5: 리모트 피어링 커넥션 생성
        if self.peers:
            remote_peering_connection_manager = RemotePeeringConnectionManager(
                self.region,
                self.config,
                self.compartment_id,
                gateway_ids,
                self.regions,
                self.peers,
            )
            remote_peering_connection_ids = remote_peering_connection_manager.create_remote_peering_connections()

        # Step 3: 라우트 테이블 생성 (프라이빗, 퍼블릭)
        route_table_manager = RouteTableManager(
            self.region,
            self.config,
            self.compartment_id,
            vcn_id,
            gateway_ids,
            self.regions,
            self.peers,
        )
        route_table_ids = route_table_manager.create_route_tables()

        # Step 4: 보안 리스트 생성 (노드, K8s API, 서비스 로드 밸런서)
        security_list_manager = SecurityListManager(
            self.region,
            self.config,
            self.compartment_id,
            vcn_id,
            self.regions,
            self.peers,
        )
        security_list_ids = security_list_manager.create_security_lists()

        # Step 5: 서브넷 생성 (서비스 로드 밸런서, 노드, K8s API)
        subnet_manager = SubnetManager(
            self.region,
            self.config,
            self.compartment_id,
            vcn_id,
            route_table_ids,
            security_list_ids,
        )
        subnet_ids = subnet_manager.create_subnets()

        return vcn_id, subnet_ids, remote_peering_connection_ids
