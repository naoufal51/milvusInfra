import pulumi
import pulumi_aws as aws

import pulumi

import pulumi
import pulumi_aws as aws
import pulumi_eks as eks
import pulumi_kubernetes as k8s
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts, LocalChartOpts
from TraefikRoute import TraefikRoute, TraefikRouteArgs
from typing import Any
import iam

# IAM roles for the node groups.
role0 = iam.create_role("role0")
role1 = iam.create_role("role1")

# cluster = eks.Cluster('milvus-eks',
#                       eks.ClusterArgs(create_oidc_provider=True,
#                                       # desired_capacity=2,
#                                       # min_size=2,
#                                       # max_size=2,
#                                       instance_type='t2.medium',
#                                       ))

cluster = eks.Cluster('milvus-eks',
                      eks.ClusterArgs(
                          skip_default_node_group=True,
                          instance_roles=[role0, role1]
                      ))

managed_node_group1 = eks.ManagedNodeGroup("managed-ng0",
                                           cluster=cluster.core,
                                           node_group_name="aws-managed-ng0",
                                           node_role_arn=role0.arn,
                                           instance_types=["t2.medium"],
                                           labels={"ondemand": "true"},
                                           opts=pulumi.ResourceOptions(parent=cluster))

managed_node_group2 = eks.ManagedNodeGroup("managed-ng1",
                                           cluster=cluster.core,
                                           node_group_name="aws-managed-ng1",
                                           node_role_arn=role1.arn,
                                           # scaling_config=aws.eks.NodeGroupScalingConfigArgs(
                                           #     desired_size=1,
                                           #     min_size=1,
                                           #     max_size=2,
                                           # ),
                                           # disk_size=20,
                                           instance_types=["t2.medium"],
                                           labels={"ondemand": "true"},
                                           # tags={"org": "pulumi"},
                                           taints={
                                               "special": {
                                                   "value": True,
                                                   "effect": "NoSchedule"
                                               }
                                           },
                                           opts=pulumi.ResourceOptions(parent=cluster))

config = pulumi.Config()

# ngxlarge = eks.NodeGroup('milvus-ng-2xlarge',
#                                 cluster=cluster,
#                                 instance_type="t2.medium",
#                                 taints={
#                                     "special": {
#                                         "value": True,
#                                         "effect": "NoSchedule"
#                                     }
#                                 }
#                                 )

# access_key = config.require_secret("access_key")
# secret_key = config.require_secret("secret_key")

provider = k8s.Provider('milvus-eks-provider-tst',
                        kubeconfig=cluster.kubeconfig,
                        opts=pulumi.ResourceOptions(parent=cluster)
                        )

milvus_namespace = k8s.core.v1.Namespace(
    'milvus-namespace',
    metadata=k8s.meta.v1.ObjectMetaArgs(name='milvus'),
    opts=pulumi.ResourceOptions(provider=provider)
)


# Install Traefik
def _fix_status(obj: Any, opts: pulumi.ResourceOptions):
    if obj.get("kind") == "CustomResourceDefinition":
        # Remove offending parameter
        del obj["status"]


# traefik = Chart(
#     "traefik",
#     LocalChartOpts(
#         path="./traefik",
#     ),
#     opts=pulumi.ResourceOptions(provider=provider)
# )

# traefik = Chart(
#     "traefik",
#     ChartOpts(
#         chart="traefik",
#         namespace='default',
#         # transformations=[_fix_status],
#         version='10.12.0',
#         fetch_opts=FetchOpts(
#             repo='https://helm.traefik.io/traefik'
#         ),
#     ),
#     opts=pulumi.ResourceOptions(provider=provider)
# )


# nginx_ingress = Chart(
#     "nginx-ingress",
#     ChartOpts(
#         chart="nginx-ingress",
#         version="1.24.4",
#         fetch_opts=FetchOpts(
#             repo="https://charts.helm.sh/stable",
#         ),
#     ),
# )

metrics_server = Chart(
    "metrics-server",
    ChartOpts(
        chart="metrics-server",
        version="3.8.2",
        fetch_opts=FetchOpts(
            repo="https://kubernetes-sigs.github.io/metrics-server/",
        ),
    ),
    opts=pulumi.ResourceOptions(provider=provider)
)

milvus = Chart(
    "milvus",
    ChartOpts(
        chart="milvus",
        namespace=milvus_namespace.metadata.name,
        values={
            "cluster": {"enabled": False},
            "etcd": {'replicaCount': 1},
            "minio": {"mode": "standalone"},
            "pulsar": {"enabled": False},
            "standalone": {
                "tolerations": {
                    "key": "special",
                    "operator": "Equal",
                    "value": True,
                    "effect": "NoSchedule"
                }
            }
        },
        fetch_opts=FetchOpts(
            repo='https://milvus-io.github.io/milvus-helm/'
        ),
    ),
    opts=pulumi.ResourceOptions(provider=provider)
)

# traefik = Chart(
#     "traefik",
#     ChartOpts(
#         chart="traefik",
#         transformations=[_fix_status],
#         # version="1.24.4",
#         version='10.12.0',
#         values={
#             "deployment": {"enabled": True},
#         },
#         fetch_opts=FetchOpts(
#             repo="https://helm.traefik.io/traefik",
#         ),
#     ),
#     opts=pulumi.ResourceOptions(provider=provider)
# )
# milvus_TraefikRoute = TraefikRoute('milvus',
#                                    TraefikRouteArgs(
#                                        prefix='/milvus',
#                                        service=milvus.get_resource('v1/Service', 'milvus', 'milvus'),
#                                        namespace=milvus_namespace.metadata.name,
#                                        stripprefix=True,
#                                    ),
#                                    opts=pulumi.ResourceOptions(provider=provider, depends_on=[milvus]),
#                                    )
# #
# aws.route53.Record("record",
#                    zone_id="Z08655752XP9PK9A7SLYU",
#                    name="ml.rhythmicai.net",
#                    type="CNAME",
#                    ttl=300,
#                    records=[traefik.get_resource("v1/Service", "traefik").status.apply(
#                        lambda s: s.load_balancer.ingress[0].hostname)]
#                    )

# data_nao = aws.ec2.Instance(f"dataNode-1",
#                             ami="ami-0d8d212151031f51c",
#                             instance_type=data_coordinator_ec2_type,
#                             key_name=key_name,
#                             subnet_id=vpc.cluster_subnet.id,
#                             vpc_security_group_ids=[vpc.cluster_sg.id],
#                             tags={
#                                 "Name": f"data_coordinator-{irange['index'] + 1}",
#                             })

pulumi.export('kubeconfig', cluster.kubeconfig)
