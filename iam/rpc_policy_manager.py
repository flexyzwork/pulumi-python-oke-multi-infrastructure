from config import Config
from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger

from .base_iam_manager import BaseIamManager

logger = global_logger


@apply_exception_handler
class RpcPolicyManager(BaseIamManager):
    def __init__(self, configs: Config):
        self.configs = configs
        self.regions = configs.regions
        self.peer_map = configs.peer_map

    def _generate_policy_details(self, policy_type, admin_group_id, target_tenancy_id, policy_name_suffix):
        """
        정책의 세부 사항을 생성하는 메서드.
        :param policy_type: 'requestor' 또는 'acceptor'
        :param admin_group_id: 정책이 속한 region의 admin_group_id
        :param target_tenancy_id: 상대 region의 tenancy_id
        """

        if policy_type == 'requestor':
            statements = [
                f'Define group Administrators as {admin_group_id}',
                f'Define tenancy Acceptor as {target_tenancy_id}',
                'Allow group Administrators to manage remote-peering-from in tenancy',
                'Endorse group Administrators to manage remote-peering-to in tenancy Acceptor',
            ]
            policy_name = f'AllowRemotePeering_Requestor_{policy_name_suffix}'
            description = 'Allow Requestor to manage remote peering requests to Acceptor'
        elif policy_type == 'acceptor':
            statements = [
                f'Define tenancy Requestor as {target_tenancy_id}',
                f'Define group Administrators as {admin_group_id}',
                'Admit group Administrators of tenancy Requestor to manage remote-peering-to in tenancy',
            ]
            policy_name = f'AllowRemotePeering_Acceptor_{policy_name_suffix}'
            description = 'Allow Acceptor to approve remote peering requests from Requestor'
        else:
            raise ValueError(f'Invalid policy type: {policy_type}')

        return policy_name, description, statements

    def create_rpc_policies(self, region, peer):
        """
        테넌시 간 피어링을 요청하는 IAM 정책 생성.
        """
        logger.info(f'Creating RPC policies: Requestor - {region}, Acceptor - {peer}')
        policy_name_suffix = f'{region}_{peer}'

        fr_iam_client = self.regions[region].iam_client
        to_iam_client = self.regions[peer].iam_client
        fr_tenancy_id = self.regions[region].tenancy
        to_tenancy_id = self.regions[peer].tenancy
        fr_admin_group_id = self.regions[region].admin_group_id

        # Requestor 정책 생성``
        fr_policy_name, fr_description, fr_statements = self._generate_policy_details(
            'requestor', fr_admin_group_id, to_tenancy_id, policy_name_suffix
        )

        # Acceptor 정책 생성
        to_policy_name, to_description, to_statements = self._generate_policy_details(
            'acceptor', fr_admin_group_id, fr_tenancy_id, policy_name_suffix
        )

        # 정책 생성 - 상위 클래스의 create_policy 메서드 사용
        self.create_policy(fr_iam_client, fr_tenancy_id, fr_policy_name, fr_description, fr_statements)
        self.create_policy(to_iam_client, to_tenancy_id, to_policy_name, to_description, to_statements)

    def create_all_policies(self):
        """
        각 테넌시 간 피어링 정책을 한 번에 설정하는 함수.
        """
        for region, peers in self.peer_map.items():
            for peer in peers:
                self.create_rpc_policies(region, peer)
