from config import Config
from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger

from .cross_tenancy_policy_manager import CrossTenancyPolicyManager
from .rpc_policy_manager import RpcPolicyManager

logger = global_logger


@apply_exception_handler
class IamManager:
    def __init__(self, configs: Config):
        self.configs = configs
        self.regions = configs.regions
        self.peer_map = configs.peer_map
        self.cross_tenancy_policy_manager = CrossTenancyPolicyManager(configs)
        self.rpc_policy_manager = RpcPolicyManager(configs)

    def create_all_iam(self):
        """모든 IAM 정책 생성"""
        if self.peer_map:
            self.cross_tenancy_policy_manager.create_all_policies()
            self.rpc_policy_manager.create_all_policies()

        logger.info('All IAM resources created successfully.')
