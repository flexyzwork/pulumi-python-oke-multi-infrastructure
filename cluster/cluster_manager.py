import os

import pulumi
import pulumi_oci as oci

from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger

from .node_pool import NodePoolManager
from .oke import OKEClusterManager

logger = global_logger


@apply_exception_handler
class ClusterManager:
    def __init__(self, region, config, compartment_id, vcn_id, subnet_ids, node_config):
        self.region = region
        self.config = config
        self.compartment_id = compartment_id
        self.vcn_id = vcn_id
        self.subnet_ids = subnet_ids
        self.node_config = node_config

    def save_kubeconfig_to_file(self, region, kubeconfig_content):
        if hasattr(kubeconfig_content, 'content'):
            kubeconfig_content = kubeconfig_content.content

        # None 체크 및 문자열 변환
        if kubeconfig_content is None:
            print(f'Error: Kubeconfig content for region {region} is None.')
            return

        file_path = os.path.expanduser(f'~/.kube/config-{region}')
        absolute_file_path = os.path.abspath(file_path)
        os.makedirs(os.path.dirname(absolute_file_path), exist_ok=True)
        with open(absolute_file_path, 'w') as kubeconfig_file:
            kubeconfig_file.write(kubeconfig_content)
        print(f'Kubeconfig saved to: {absolute_file_path}')

    def create_cluster(self):
        # Step 6: OKE 클러스터 생성
        cluster_manager = OKEClusterManager(
            self.region,
            self.config,
            self.compartment_id,
            self.vcn_id,
            self.subnet_ids,
            self.node_config,
        )
        cluster_id = cluster_manager.create_oke_cluster()

        # Step 7: OKE 노드 풀 생성
        node_pool_manager = NodePoolManager(
            self.region,
            self.config,
            self.compartment_id,
            self.subnet_ids,
            cluster_id,
            self.node_config,
        )
        node_pool_id = node_pool_manager.create_node_pool()

        # 클러스터 ID가 생성되면 이를 사용하여 kubeconfig 가져오기
        self.kubeconfig = (
            pulumi.Output.all(cluster_id, node_pool_id)
            .apply(
                lambda outputs: oci.containerengine.get_cluster_kube_config(
                    cluster_id=outputs[0],
                    token_version='2.0.0',
                    opts=pulumi.InvokeOptions(provider=self.config.provider),
                )
            )
            .apply(lambda kubeconfig: self.save_kubeconfig_to_file(self.region, kubeconfig))
        )

        return cluster_id, node_pool_id
