import json
import os

import oci as oci_sdk  # type: ignore
import pulumi
import pulumi_oci as oci  # type: ignore

from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger

from . import Config, NodeConfig, RegionResources

logger = global_logger


@apply_exception_handler
class ConfigManager:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.configs = self._load_config()

    def _convert_peer_map(self, data):
        """peer_map을 bidirectional peer map으로 변환"""
        if not isinstance(data, dict) or not all(isinstance(value, list) for value in data.values()):
            raise ValueError('Invalid input data. Expected a dictionary with list values.')

        result = {}
        for key, values in data.items():
            if not values:
                result[key] = []
            else:
                for value in values:
                    result.setdefault(key, set()).add(value)
                    result.setdefault(value, set()).add(key)
        return {key: list(values) for key, values in result.items()}

    def _get_pulumi_config_value(self, key, is_secret=False):
        """Pulumi Config에서 값을 가져옵니다"""
        try:
            config = pulumi.Config()
            if is_secret:
                return config.require_secret(key)
            else:
                return config.require(key)
        except Exception as e:
            logger.warning(f'Failed to get Pulumi config value for {key}: {e}')
            return None

    def _load_config(self):
        """설정 파일을 및 프로파일명 기준 ~/.oci/config 값을 로드"""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f'Configuration file not found at: {self.config_path}')
            with open(self.config_path) as config_file:
                config_data = json.load(config_file)

                # Pulumi Config에서 SSH 공개키 가져오기
                ssh_public_key = self._get_pulumi_config_value('ssh_public_key', is_secret=True)

                # SSH 공개키가 없으면 에러 발생
                if ssh_public_key is None:
                    raise ValueError(
                        'SSH public key not found in Pulumi config. '
                        'Please set it using: '
                        'pulumi config set --secret ssh_public_key "your-ssh-key"'
                    )

                # NodeConfig 및 RegionResources를 OCI config 정보로 초기화
                configs = Config(
                    peer_map=config_data.get('peer_map', {}),
                    peer_bi_map=self._convert_peer_map(config_data.get('peer_map', {})),
                    node=NodeConfig(
                        **config_data.get('node'),
                        ssh_public_key=os.getenv('SSH_PUBLIC_KEY'),
                    ),
                    regions={
                        region: self._initialize_region_resources(region, region_data)
                        for region, region_data in config_data.get('regions', {}).items()
                    },
                    home_region=config_data.get('home_region', ''),
                )
                # logging config
                logger.info(f'{"-" * 30} Loaded Configurations {"-" * 30}')
                for config_name, config_data in configs.__dict__.items():
                    if config_name == 'regions':
                        for region, region_resources in config_data.items():
                            logger.info(f'{region}: {region_resources}')
                            logger.info('-' * 64)
                    else:
                        logger.info(f'{config_name}: {config_data}')
                        logger.info('-' * 64)
                return configs

        except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
            logger.error(f'Failed to load configuration: {e}')
            raise

    def _initialize_region_resources(self, region, region_data):
        """프로파일명을 기준으로 ~/.oci/config에서 지역별 리소스 초기화"""
        try:
            # 프로파일명은 region과 동일하게 사용
            oci_config = oci_sdk.config.from_file(profile_name=region)
            iam_client = oci_sdk.identity.IdentityClient(oci_config)
            virtual_network_client = oci_sdk.core.VirtualNetworkClient(oci_config)
            provider = oci.Provider(f'provider_{region}', config_file_profile=region)

            return RegionResources(
                **region_data,
                user=oci_config['user'],
                fingerprint=oci_config['fingerprint'],
                tenancy=oci_config['tenancy'],
                region_name=oci_config['region'],
                key_file=oci_config['key_file'],
                iam_client=iam_client,
                virtual_network_client=virtual_network_client,
                provider=provider,
            )
        except Exception as e:
            logger.error(f'Failed to initialize region resources for {region}: {e}')
            raise
