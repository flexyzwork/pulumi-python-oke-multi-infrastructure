import pulumi_oci as oci

from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger
from utils.resource_helper import create_resource

logger = global_logger


@apply_exception_handler
class OKEClusterManager:
    """
    OKE 클러스터 생성 및 관리 클래스
    """

    def __init__(self, region, config, compartment_id, vcn_id, subnet_ids, node_config):
        self.region = region
        self.config = config
        self.compartment_id = compartment_id
        self.vcn_id = vcn_id
        self.subnet_ids = subnet_ids
        self.node_config = node_config
        self.cluster_id = None

    def create_oke_cluster(self):
        """
        OKE 클러스터를 생성하는 메소드
        """
        return create_resource(
            oci.containerengine.Cluster,
            self.config.provider,
            self.region,
            self.compartment_id,
            name=f'{self.region}-cluster',
            kubernetes_version=self.node_config.kubernetes_version,
            vcn_id=self.vcn_id,
            options=oci.containerengine.ClusterOptionsArgs(
                service_lb_subnet_ids=[self.subnet_ids.service_lb_subnet_id]
            ),
            endpoint_config=oci.containerengine.ClusterEndpointConfigArgs(
                is_public_ip_enabled=True, subnet_id=self.subnet_ids.k8s_api_subnet_id
            ),
            cluster_pod_network_options=[
                oci.containerengine.ClusterClusterPodNetworkOptionArgs(cni_type='OCI_VCN_IP_NATIVE')
            ],
            freeform_tags={'OKEclusterName': f'oke{self.region}'},
            type='BASIC_CLUSTER',
        )
