from dataclasses import dataclass, field

import oci as oci_sdk  # type: ignore
import pulumi_oci as oci  # type: ignore
from cryptography.hazmat.primitives.asymmetric import rsa
from pulumi import Output


@dataclass
class NodeConfig:
    kubernetes_version: str
    node_pool_name: str
    node_pool_size: int
    node_shape: str
    node_memory_gbs: int
    node_ocpus: int
    ssh_public_key: rsa.RSAPrivateKey | str | None = field(repr=False, compare=False)


@dataclass
class RegionResources:
    # 기본값이 없는 필드들
    availability_domain: str
    service_cidr: str
    service_id: str
    image_id: str
    vcn_cidr_block: str
    node_subnet_cidr_block: str
    k8s_api_subnet_cidr_block: str
    service_lb_subnet_cidr_block: str
    admin_group_id: str

    # 기본값이 있는 필드들 (Optional로 설정)
    user: str | None = None
    fingerprint: str | None = None
    tenancy: str | None = None
    region_name: str | None = None
    key_file: str | None = None

    # 클라이언트 필드들 (Optional로 설정)
    iam_client: oci_sdk.identity.IdentityClient | None = None
    virtual_network_client: oci_sdk.core.VirtualNetworkClient | None = None
    provider: oci.Provider | None = None


@dataclass
class Config:
    peer_map: dict[str, list[str]] = field(default_factory=dict)
    peer_bi_map: dict[str, list[str]] = field(default_factory=dict)
    node: NodeConfig = field(
        default_factory=lambda: NodeConfig(
            kubernetes_version='',
            node_pool_name='',
            node_pool_size=0,
            node_shape='',
            node_memory_gbs=0,
            node_ocpus=0,
            ssh_public_key='',
        )
    )
    regions: dict[str, RegionResources] = field(default_factory=dict)
    home_region: str | None = None


@dataclass
class GatewayIDs:
    nat_gateway_id: Output | str | None = None
    internet_gateway_id: Output | str | None = None
    service_gateway_id: Output | str | None = None
    dynamic_routing_gateway_id: Output | str | None = None


@dataclass
class RouteTableIDs:
    route_table_private_id: Output | str | None = None
    route_table_public_id: Output | str | None = None


@dataclass
class SecurityListIDs:
    node_security_list_id: Output | str | None = None
    k8s_api_security_list_id: Output | str | None = None
    service_lb_security_list_id: Output | str | None = None


@dataclass
class SubnetIDs:
    service_lb_subnet_id: Output | str | None = None
    node_subnet_id: Output | str | None = None
    k8s_api_subnet_id: Output | str | None = None
