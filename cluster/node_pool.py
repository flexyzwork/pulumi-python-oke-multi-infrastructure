import pulumi_oci as oci

from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger
from utils.resource_helper import create_resource

logger = global_logger


@apply_exception_handler
class NodePoolManager:
    """
    OKE 노드 풀 생성 및 관리 클래스
    """

    def __init__(self, region, config, compartment_id, subnet_ids, cluster_id, node_config):
        self.region = region
        self.config = config
        self.compartment_id = compartment_id
        self.subnet_ids = subnet_ids
        self.cluster_id = cluster_id
        self.node_config = node_config

    def create_node_config_details(self):
        """
        OKE 노드 풀의 구성 세부 정보를 생성하는 메소드
        """
        logger.info(f'availability_domain={self.config.availability_domain}')
        return oci.containerengine.NodePoolNodeConfigDetailsArgs(
            freeform_tags={'oke_node_pool_name': self.node_config.node_pool_name},
            node_pool_pod_network_option_details=oci.containerengine.NodePoolNodeConfigDetailsNodePoolPodNetworkOptionDetailsArgs(
                pod_subnet_ids=[self.subnet_ids.node_subnet_id],
                cni_type='OCI_VCN_IP_NATIVE',
            ),
            placement_configs=[
                oci.containerengine.NodePoolNodeConfigDetailsPlacementConfigArgs(
                    availability_domain=self.config.availability_domain,
                    subnet_id=self.subnet_ids.node_subnet_id,
                )
            ],
            size=self.node_config.node_pool_size,
        )

    def create_node_pool(self):
        """
        OKE 노드 풀을 생성하는 메소드
        """
        logger.info('Creating OKE node pool')

        return create_resource(
            oci.containerengine.NodePool,
            self.config.provider,
            self.region,
            self.compartment_id,
            cluster_id=self.cluster_id,
            freeform_tags={'OKEnodePoolName': self.node_config.node_pool_name},
            initial_node_labels=[
                oci.containerengine.NodePoolInitialNodeLabelArgs(key='name', value=f'nodepool{self.region}')
            ],
            kubernetes_version=self.node_config.kubernetes_version,
            name=self.node_config.node_pool_name,
            node_config_details=self.create_node_config_details(),
            node_eviction_node_pool_settings=oci.containerengine.NodePoolNodeEvictionNodePoolSettingsArgs(
                eviction_grace_duration='PT60M'  # 노드 제거 설정 (Node eviction settings)
            ),
            node_shape=self.node_config.node_shape,
            node_shape_config=oci.containerengine.NodePoolNodeShapeConfigArgs(
                memory_in_gbs=self.node_config.node_memory_gbs,
                ocpus=self.node_config.node_ocpus,
            ),
            node_source_details=oci.containerengine.NodePoolNodeSourceDetailsArgs(
                image_id=self.config.image_id, source_type='IMAGE'
            ),
            ssh_public_key=self.node_config.ssh_public_key,  # SSH 공개 키
        )
