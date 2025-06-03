import oci as oci_sdk  # type: ignore

from utils.exception_handler import apply_exception_handler
from utils.logger import global_logger

logger = global_logger


@apply_exception_handler
class BaseIamManager:
    def create_policy(self, iam_client, compartment_id, policy_name, description, statements):
        """IAM 정책 생성 (이미 존재하는 경우 예외처리)"""
        try:
            policy_details = oci_sdk.identity.models.CreatePolicyDetails(
                compartment_id=compartment_id,
                name=policy_name,
                description=description,
                statements=statements,
            )
            iam_client.create_policy(policy_details)
            logger.info(f'IAM policy {policy_name} created successfully.')
        except oci_sdk.exceptions.ServiceError as e:
            if e.status == 409:  # Conflict
                logger.info(f'IAM policy {policy_name} already exists.')
            else:
                logger.error(f'Failed to create policy {policy_name}: {e}')
                raise e
        return policy_details
