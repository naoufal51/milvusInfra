
import pulumi
import pulumi_eks as eks
import pulumi_kubernetes as k8s
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts, LocalChartOpts

import iam

# IAM roles for the node groups.
role0 = iam.create_role("role0")
role1 = iam.create_role("role1")
config = pulumi.Config()

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



# provider = k8s.Provider('milvus-eks-provider-tst',
#                         kubeconfig=cluster.kubeconfig,
#                         opts=pulumi.ResourceOptions(parent=cluster)
#                         )




pulumi.export('kubeconfig', cluster.kubeconfig)
