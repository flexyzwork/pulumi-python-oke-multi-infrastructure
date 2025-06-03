import oci as oci_sdk
import pulumi
import pulumi_oci as oci

from config import RouteTableIDs, SecurityListIDs, SubnetIDs
from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger
from utils.resource_helper import create_resource

logger = global_logger


@apply_exception_handler
class SubnetManager:
    """
    서브넷 생성 및 관리 클래스
    """

    def __init__(self, region, config, compartment_id, vcn_id, route_table_ids, security_list_ids):
        self.region = region
        self.config = config
        self.compartment_id = compartment_id
        self.vcn_id = vcn_id
        self.route_table_ids: RouteTableIDs = route_table_ids
        self.security_list_ids: SecurityListIDs = security_list_ids
        self.subnet_ids = SubnetIDs()

    def create_service_lb_subnet(self):
        subnet_id = create_resource(
            oci.core.Subnet,
            self.config.provider,
            self.region,
            self.compartment_id,
            'service-lb',
            vcn_id=self.vcn_id,
            cidr_block=self.config.service_lb_subnet_cidr_block,
            dns_label='lbsub',
            prohibit_public_ip_on_vnic=False,
            route_table_id=self.route_table_ids.route_table_public_id,  # 수정함 (이게 서비스 노출 안 됐던 원인인 듯)
            security_list_ids=[self.security_list_ids.service_lb_security_list_id],  # ingress가 제대로 안 되서 수정
        )

        # Output 객체에서 서브넷 ID를 받아 NLB 삭제 함수 호출
        subnet_id.apply(self.check_nlb)

        # pulumi.Output.from_input(subnet_id).apply(self.check_and_delete_nlb)

        return subnet_id

    def create_oci_client(self):
        """OCI 클라이언트 생성"""
        oci_config = oci_sdk.config.from_file(profile_name=self.region)
        return oci_sdk.network_load_balancer.NetworkLoadBalancerClient(oci_config)

    def check_nlb(self, subnet_id):
        """서브넷에 연결된 NLB 조회"""

        # Pulumi Output 객체를 처리하기 위한 apply 사용
        def delete_nlb(compartment_id, subnet_id):
            try:
                nlb_client = self.create_oci_client()

                # 컴파트먼트 내 모든 NLB 목록 가져오기
                response = nlb_client.list_network_load_balancers(compartment_id=compartment_id)
                nlb_list = response.data.items  # type: ignore # data 속성에서 NLB 리스트 가져오기

                # 서브넷과 연결된 NLB 삭제
                for nlb in nlb_list:
                    if nlb.subnet_id == subnet_id:
                        logger.info(
                            f'Before delete service-lb Subnet, have to delete NLB: {nlb.display_name}({nlb.id})'
                        )
                        # nlb_client.delete_network_load_balancer(network_load_balancer_id=nlb.id)

            except oci_sdk.exceptions.ServiceError as e:
                print(f'Service error: {e.message}')
            except Exception as e:
                print(f'An error occurred: {e!s}')

        # compartment_id와 subnet_ocid가 Pulumi Output 객체라면 apply를 통해 값을 전달
        pulumi.Output.all(self.compartment_id, subnet_id).apply(lambda args: delete_nlb(args[0], args[1]))

    def create_node_subnet(self):
        return create_resource(
            oci.core.Subnet,
            self.config.provider,
            self.region,
            self.compartment_id,
            'node',
            vcn_id=self.vcn_id,
            cidr_block=self.config.node_subnet_cidr_block,
            dns_label='nodesub',
            prohibit_public_ip_on_vnic=True,
            route_table_id=self.route_table_ids.route_table_private_id,
            security_list_ids=[self.security_list_ids.node_security_list_id],
        )

    def create_k8s_api_subnet(self):
        return create_resource(
            oci.core.Subnet,
            self.config.provider,
            self.region,
            self.compartment_id,
            'k8s-api',
            vcn_id=self.vcn_id,
            cidr_block=self.config.k8s_api_subnet_cidr_block,
            dns_label='apisub',
            prohibit_public_ip_on_vnic=False,
            route_table_id=self.route_table_ids.route_table_public_id,  # kubectrl 통신이 안 되서 수정
            security_list_ids=[
                self.security_list_ids.node_security_list_id,
                self.security_list_ids.k8s_api_security_list_id,
            ],
        )

    def create_subnets(self):
        """
        모든 서브넷을 생성하는 메소드
        """
        self.subnet_ids.service_lb_subnet_id = self.create_service_lb_subnet()
        self.subnet_ids.node_subnet_id = self.create_node_subnet()
        self.subnet_ids.k8s_api_subnet_id = self.create_k8s_api_subnet()
        return self.subnet_ids
