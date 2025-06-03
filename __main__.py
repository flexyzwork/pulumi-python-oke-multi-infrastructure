import pulumi

from cluster.cluster_manager import ClusterManager
from compartment import CompartmentManager
from config import ConfigManager
from iam import IamManager
from network import NetworkManager, PublicIpManager, RemotePeeringConnector
from utils.logger import global_logger

logger = global_logger


def main(config_manager: ConfigManager):
    # 설정 파일 로드
    configs = config_manager.configs
    regions = configs.regions
    peer_map = configs.peer_map
    peer_bi_map = configs.peer_bi_map
    region_rpcs, cluster_ids, compartment_ids, public_ips = {}, {}, {}, {}

    # 지역별로 구획, 네트워크, oke cluster 생성
    for region, config, peers in zip(regions.keys(), regions.values(), peer_bi_map.values(), strict=False):
        compartment_manager = CompartmentManager(region, config)
        compartment_id = compartment_manager.create_compartment()
        compartment_ids[region] = compartment_id
        network_manager = NetworkManager(region, config, compartment_id, regions, peers)
        vcn_id, subnet_ids, remote_peering_connection_ids = network_manager.create_network()
        region_rpcs[region] = remote_peering_connection_ids
        public_ip_manager = PublicIpManager(region, config, compartment_id)
        public_ips[region] = public_ip_manager.reserve_public_ip()
        # 특정 리전의 oke를 초기화하고자 할 경우 아래 리스트에 대상 region 추가
        regions_to_delete_oke = ['', '', '']
        if region not in regions_to_delete_oke:
            cluster_manager = ClusterManager(region, config, compartment_id, vcn_id, subnet_ids, configs.node)
            cluster_ids[region] = cluster_manager.create_cluster()

    pulumi.Output.all(region_rpcs).apply(lambda outputs: connect_peering_connections(outputs[0], peer_map, configs))


def connect_peering_connections(region_rpcs, peer_map, configs):
    logger.info('Connecting peering connections...')

    # IAM 생성
    iam_manager = IamManager(configs)
    iam_manager.create_all_iam()

    remote_peering_connection_connector = RemotePeeringConnector(region_rpcs, peer_map, configs)
    remote_peering_connection_connector.connect_all_peers()


if __name__ == '__main__':
    # main()
    config_manager = ConfigManager(config_path='config.json')
    main(config_manager)
