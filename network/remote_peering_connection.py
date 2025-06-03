# import time

import time

import oci as oci_sdk
import pulumi_oci as oci

from config import Config
from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger
from utils.resource_helper import create_resource

logger = global_logger


@apply_exception_handler
class RemotePeeringConnectionManager:
    def __init__(self, region, config, compartment_id, gateway_ids, regions, peers):
        self.region = region
        self.config = config
        self.compartment_id = compartment_id
        self.dynamic_routing_gateway_id = gateway_ids.dynamic_routing_gateway_id
        self.regions = regions
        self.peers = peers
        self.remote_peering_connection_ids = {}

    def create_remote_peering_connection(self, peer):
        """RPC 생성"""
        return create_resource(
            oci.core.RemotePeeringConnection,
            self.config.provider,
            self.region,
            self.compartment_id,
            f'{self.region}-{peer}',
            drg_id=self.dynamic_routing_gateway_id,
            peer_region_name=self.regions[peer].region_name,
        )

    def create_remote_peering_connections(self):
        for peer in self.peers:
            self.remote_peering_connection_ids[peer] = self.create_remote_peering_connection(peer)
        return self.remote_peering_connection_ids


@apply_exception_handler
class RemotePeeringConnector:
    def __init__(self, region_rpcs, peer_map, configs: Config):
        self.region_rpcs = region_rpcs
        self.peer_map = peer_map
        self.configs = configs

    def connect_peer(
        self,
        virtual_network_client,
        region,
        rpc_id,
        peer,
        peer_rpc_id,
        peer_region_name,
    ):
        """
        RPC 연결을 처리하는 함수.
        """
        try:
            # RPC 상태 확인
            rpc_details = virtual_network_client.get_remote_peering_connection(rpc_id).data  # type: ignore
            rpc_status = rpc_details.lifecycle_state
            peering_status = rpc_details.peering_status

            if rpc_status == 'AVAILABLE' and rpc_details.peer_id == peer_rpc_id and peering_status == 'PEERED':
                print(f'RPC {rpc_id} is already connected to {peer_rpc_id}. Skipping.')
                return

            elif rpc_status == 'PENDING':
                print(f'RPC {rpc_id} is in PENDING state. Waiting for it to become available...')
                time.sleep(60)  # 대기 시간 설정 (예: 60초)
                rpc_details = virtual_network_client.get_remote_peering_connection(rpc_id).data  # type: ignore
                if rpc_details.lifecycle_state != 'AVAILABLE':
                    raise Exception(f'RPC {rpc_id} is still not available after waiting.')

            rpc_name = f'rpc_{region}_{peer}'
            connect_rpc_details = oci_sdk.core.models.ConnectRemotePeeringConnectionsDetails(
                peer_id=peer_rpc_id,
                peer_region_name=peer_region_name,
            )
            virtual_network_client.connect_remote_peering_connections(
                remote_peering_connection_id=rpc_id,
                connect_remote_peering_connections_details=connect_rpc_details,
            )
            logger.info(f'RPC {region} to {peer_rpc_id} in region {peer_region_name} connected Successfully.')
        except oci_sdk.exceptions.ServiceError as e:
            if e.status == 409:  # Conflict
                logger.info(f'IAM policy {rpc_name} already exists.')
            else:
                logger.error(f'Failed to create policy {rpc_name}: {e}')
                raise e

    def connect_all_peers(self):
        """
        모든 RPC 연결을 처리하는 함수.
        """
        for region, peers in self.peer_map.items():
            if len(peers) == 0:
                continue
            virtual_network_client = self.configs.regions[region].virtual_network_client
            for peer in peers:
                rpc_id = self.region_rpcs[region][peer]
                peer_rpc_id = self.region_rpcs[peer][region]
                peer_region_name = self.configs.regions[peer].region_name
                self.connect_peer(
                    virtual_network_client,
                    region,
                    rpc_id,
                    peer,
                    peer_rpc_id,
                    peer_region_name,
                )
