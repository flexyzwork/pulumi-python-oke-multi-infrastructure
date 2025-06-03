import pulumi_oci as oci

from config import SecurityListIDs
from utils.resource_helper import create_resource


class SecurityListManager:
    """
    보안 리스트 생성 및 관리 클래스
    """

    def __init__(self, region, config, compartment_id, vcn_id, regions, peers=None):
        self.region = region
        self.config = config
        self.compartment_id = compartment_id
        self.vcn_id = vcn_id
        self.regions = regions
        self.peers = peers
        self.security_list_ids = SecurityListIDs()

    def create_node_security_list(self):
        """
        노드용 보안 리스트 생성 메소드
        """
        return create_resource(
            oci.core.SecurityList,
            self.config.provider,
            self.region,
            self.compartment_id,
            'node',
            vcn_id=self.vcn_id,
            ingress_security_rules=self.get_node_ingress_rules(),
            egress_security_rules=self.get_node_egress_rules(),
        )

    def create_k8s_api_security_list(self):
        """
        Kubernetes API 보안 리스트 생성 메소드
        """
        return create_resource(
            oci.core.SecurityList,
            self.config.provider,
            self.region,
            self.compartment_id,
            'k8s-api',
            vcn_id=self.vcn_id,
            ingress_security_rules=self.get_k8s_api_ingress_rules(),
            egress_security_rules=self.get_k8s_api_egress_rules(),
        )

    def create_service_lb_security_list(self):
        """
        서비스 로드 밸런서 보안 리스트 생성 메소드
        """
        return create_resource(
            oci.core.SecurityList,
            self.config.provider,
            self.region,
            self.compartment_id,
            'service-lb',
            vcn_id=self.vcn_id,
        )

    # 공통 규칙 생성 메소드
    # def path_discovery_rule(self, source_or_dest, cidr_block):
    #     """
    #     Path discovery 규칙 생성 메소드
    #     """
    #     return {
    #         'description': 'Path discovery',
    #         'icmp_options': {
    #             'code': 4,
    #             'type': 3
    #         },
    #         'protocol': '1',
    #         source_or_dest: cidr_block,
    #         'stateless': False
    #     }

    # def node_tcp_rule(self):
    #     """
    #     노드 TCP 규칙 생성 메소드
    #     """
    #     return {
    #         'description': 'TCP access from Kubernetes Control Plane',
    #         'protocol': '6',
    #         'source': self.config.k8s_api_subnet_cidr_block,
    #         'stateless': False
    #     }

    # 노드용 Ingress 규칙 생성 메소드
    def get_node_ingress_rules(self):
        """
        노드용 Ingress 규칙 생성
        """
        ingress_rules = [
            oci.core.SecurityListIngressSecurityRuleArgs(
                description='Path discovery',
                icmp_options=oci.core.SecurityListIngressSecurityRuleIcmpOptionsArgs(
                    code=4,
                    type=3,
                ),
                protocol='1',
                source=self.config.k8s_api_subnet_cidr_block,
                source_type='CIDR_BLOCK',
            ),
            oci.core.SecurityListIngressSecurityRuleArgs(
                description='Inbound SSH traffic to worker nodes',
                protocol='6',
                source='0.0.0.0/0',
                source_type='CIDR_BLOCK',
                tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                    max=22,
                    min=22,
                ),
            ),
            oci.core.SecurityListIngressSecurityRuleArgs(
                description='Allow pods on one worker node to communicate with pods on other worker nodes',
                protocol='all',
                source=self.config.node_subnet_cidr_block,
                source_type='CIDR_BLOCK',
            ),
            oci.core.SecurityListIngressSecurityRuleArgs(
                description='TCP access from Kubernetes Control Plane',
                protocol='6',
                source=self.config.k8s_api_subnet_cidr_block,
                source_type='CIDR_BLOCK',
            ),
            # self.path_discovery_rule('source', self.config.k8s_api_subnet_cidr_block),
            # self.node_tcp_rule(),
            # {
            #     'description': 'Inbound SSH traffic to worker nodes',
            #     'protocol': '6',
            #     'source': '0.0.0.0/0',
            #     'stateless': False
            # },
            # {
            #     'description': 'Allow pods on one worker node to communicate with pods on other worker nodes',
            #     'protocol': 'all',
            #     'source': self.config.node_subnet_cidr_block,
            #     'stateless': False
            # },
        ]

        if self.peers:
            for peer in self.peers:
                peer_rule = [
                    {
                        'description': f'Allow communication with peer {peer}',
                        'protocol': 'all',
                        'source': self.regions[peer].vcn_cidr_block,  # TODO: 세분화해야 하는지 확인
                        'stateless': False,
                    },
                ]
                ingress_rules.extend(peer_rule)
        return ingress_rules

    # 노드용 Egress 규칙 생성 메소드
    def get_node_egress_rules(self):
        """
        노드용 Egress 규칙 생성
        """
        egress_rules = [
            oci.core.SecurityListEgressSecurityRuleArgs(
                description='Kubernetes worker to control plane communication',
                destination=self.config.k8s_api_subnet_cidr_block,
                destination_type='CIDR_BLOCK',
                protocol='6',
                tcp_options=oci.core.SecurityListEgressSecurityRuleTcpOptionsArgs(
                    max=12250,
                    min=12250,
                ),
            ),
            oci.core.SecurityListEgressSecurityRuleArgs(
                description='Worker Nodes access to Internet',
                destination='0.0.0.0/0',
                destination_type='CIDR_BLOCK',
                protocol='all',
            ),
            oci.core.SecurityListEgressSecurityRuleArgs(
                description='Access to Kubernetes API Endpoint',
                destination=self.config.k8s_api_subnet_cidr_block,
                destination_type='CIDR_BLOCK',
                protocol='6',
                tcp_options=oci.core.SecurityListEgressSecurityRuleTcpOptionsArgs(
                    max=6443,
                    min=6443,
                ),
            ),
            oci.core.SecurityListEgressSecurityRuleArgs(
                description='Path discovery',
                destination=self.config.k8s_api_subnet_cidr_block,
                destination_type='CIDR_BLOCK',
                icmp_options=oci.core.SecurityListEgressSecurityRuleIcmpOptionsArgs(
                    code=4,
                    type=3,
                ),
                protocol='1',
            ),
            oci.core.SecurityListEgressSecurityRuleArgs(
                description='ICMP Access from Kubernetes Control Plane',
                destination='0.0.0.0/0',
                destination_type='CIDR_BLOCK',
                icmp_options=oci.core.SecurityListEgressSecurityRuleIcmpOptionsArgs(
                    code=4,
                    type=3,
                ),
                protocol='1',
            ),
            oci.core.SecurityListEgressSecurityRuleArgs(
                description='Allow nodes to communicate with OKE to ensure correct start-up and continued functioning',
                destination=self.config.service_cidr,
                destination_type='SERVICE_CIDR_BLOCK',
                protocol='6',
                tcp_options=oci.core.SecurityListEgressSecurityRuleTcpOptionsArgs(
                    max=443,
                    min=443,
                ),
            ),
            oci.core.SecurityListEgressSecurityRuleArgs(
                description='Allow pods on one worker node to communicate with pods on other worker nodes',
                destination=self.config.node_subnet_cidr_block,
                destination_type='CIDR_BLOCK',
                protocol='all',
            ),
            # self.path_discovery_rule('destination', self.config.k8s_api_subnet_cidr_block),
            # {
            #     'description': 'Allow nodes to communicate with OKE',
            #     'destination': self.config.service_cidr,
            #     'destination_type': 'SERVICE_CIDR_BLOCK',
            #     'protocol': '6',
            #     'stateless': False
            # },
            # {
            #     'description': 'Allow pods on one worker node to communicate with pods on other worker nodes',
            #     'destination': self.config.node_subnet_cidr_block,
            #     'destination_type': 'CIDR_BLOCK',
            #     'protocol': 'all',
            #     'stateless': False
            # },
            # {
            #     'description': 'Access to Kubernetes API Endpoint',
            #     'destination': self.config.k8s_api_subnet_cidr_block,
            #     'destination_type': 'CIDR_BLOCK',
            #     'protocol': '6',
            #     'stateless': False
            # },
            # {
            #     'description': 'Worker Nodes access to Internet',
            #     'destination': '0.0.0.0/0',
            #     'destination_type': 'CIDR_BLOCK',
            #     'protocol': 'all',
            #     'stateless': False
            # },
        ]
        if self.peers:
            for peer in self.peers:
                peer_rule = [
                    {
                        'description': f'Worker Nodes access to peer {peer}',
                        'destination': self.regions[peer].vcn_cidr_block,  # TODO: 세분화해야 하는지 확인
                        'destination_type': 'CIDR_BLOCK',
                        'protocol': 'all',
                        'stateless': False,
                    },
                ]
                egress_rules.extend(peer_rule)
        return egress_rules

    # Kubernetes API Ingress 규칙 생성 메소드
    def get_k8s_api_ingress_rules(self):
        """
        Kubernetes API Ingress 규칙 생성
        """
        return [
            oci.core.SecurityListIngressSecurityRuleArgs(
                description='Kubernetes worker to control plane communication',
                protocol='6',
                source=self.config.node_subnet_cidr_block,
                source_type='CIDR_BLOCK',
                tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                    max=12250,
                    min=12250,
                ),
            ),
            oci.core.SecurityListIngressSecurityRuleArgs(
                description='Kubernetes worker to Kubernetes API endpoint communication',
                protocol='6',
                source=self.config.node_subnet_cidr_block,
                source_type='CIDR_BLOCK',
                tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                    max=6443,
                    min=6443,
                ),
            ),
            oci.core.SecurityListIngressSecurityRuleArgs(
                description='External access to Kubernetes API endpoint',
                protocol='6',
                source='0.0.0.0/0',
                source_type='CIDR_BLOCK',
                tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                    max=6443,
                    min=6443,
                ),
            ),
            oci.core.SecurityListIngressSecurityRuleArgs(
                description='Path discovery',
                icmp_options=oci.core.SecurityListIngressSecurityRuleIcmpOptionsArgs(
                    code=4,
                    type=3,
                ),
                protocol='1',
                source=self.config.node_subnet_cidr_block,
                source_type='CIDR_BLOCK',
            ),
            # self.path_discovery_rule('source', self.config.node_subnet_cidr_block), {
            #     'description': 'External access to Kubernetes API endpoint',
            #     'protocol': '6',
            #     'source': '0.0.0.0/0',
            #     'stateless': False
            # }, {
            #     'description': 'Kubernetes worker to Kubernetes API endpoint communication',
            #     'protocol': '6',
            #     'source': self.config.node_subnet_cidr_block,
            #     'stateless': False
            # }
        ]

    # Kubernetes API Egress 규칙 생성 메소드
    def get_k8s_api_egress_rules(self):
        """
        Kubernetes API Egress 규칙 생성
        """
        return [
            oci.core.SecurityListEgressSecurityRuleArgs(
                description='Path discovery',
                destination=self.config.node_subnet_cidr_block,
                destination_type='CIDR_BLOCK',
                icmp_options=oci.core.SecurityListEgressSecurityRuleIcmpOptionsArgs(
                    code=4,
                    type=3,
                ),
                protocol='1',
            ),
            oci.core.SecurityListEgressSecurityRuleArgs(
                description='Allow Kubernetes Control Plane to communicate with OKE',
                destination=self.config.service_cidr,
                destination_type='SERVICE_CIDR_BLOCK',
                protocol='6',
                tcp_options=oci.core.SecurityListEgressSecurityRuleTcpOptionsArgs(
                    max=443,
                    min=443,
                ),
            ),
            oci.core.SecurityListEgressSecurityRuleArgs(
                description='All traffic to worker nodes',
                destination=self.config.node_subnet_cidr_block,
                destination_type='CIDR_BLOCK',
                protocol='6',
            ),
            # self.path_discovery_rule('destination', self.config.node_subnet_cidr_block),
            # {
            #     'description': 'Allow Kubernetes Control Plane to communicate with OKE',
            #     'destination': self.config.service_cidr,
            #     'destination_type': 'SERVICE_CIDR_BLOCK',
            #     'protocol': '6',
            #     'stateless': False
            # },
            # {
            #     'description': 'All traffic to worker nodes',
            #     'destination': self.config.node_subnet_cidr_block,
            #     'destination_type': 'CIDR_BLOCK',
            #     'protocol': '6',
            #     'stateless': False
            # },
        ]

    def create_security_lists(self):
        """
        모든 보안 리스트를 생성하는 메소드
        """
        self.security_list_ids.node_security_list_id = self.create_node_security_list()
        self.security_list_ids.k8s_api_security_list_id = self.create_k8s_api_security_list()
        self.security_list_ids.service_lb_security_list_id = self.create_service_lb_security_list()
        return self.security_list_ids
