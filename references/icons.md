# Icon catalog

Curated vendor icons for the `drawio` skill. Pass a **key** from these tables to
`icon_box()` or `icon_node()`; the helper turns it into the right style string.

```python
icon_box(40, 80, 220, 60, "Order Handler", fill=..., icon="aws-lambda")
icon_node(40, 80, "Order Handler", icon="aws-lambda")
```

Every name here is verified against draw.io Desktop 31.1.8. `scripts/list_icons.py
--verify` re-checks them against your local install; `--search <term>` finds a key.

**Not every logo is here.** These are the ~130 most-used services. draw.io ships
about 11,500 names in total — `--dump-names --family aws` lists them all, and any
of them works. For a logo draw.io has no stencil for (Snowflake, Databricks, a
client's brand mark), use `svg_icon("path/to/logo.svg")` instead.

**Dark mode.** The `fill` column is the vendor's brand colour. AWS and Kubernetes
render as a coloured tile with a white glyph, so they read on either canvas.
GCP and Cisco are monochrome and take a `fill` you can theme with `ld()`. Azure
icons are fixed-colour SVG files and cannot be recoloured — put one in an
`icon_box()` if it washes out.


## AWS — `aws-*` (51)

Rendered through the `resourceIcon` tile wrapper. The `fill` is AWS's own category colour — orange for compute, green for storage, blue-violet for networking and analytics, red for security.

| Service | Key | draw.io name | Fill |
| --- | --- | --- | --- |
| Application Load Balancer | `aws-alb` | `application_load_balancer` | `#8C4FFF` |
| Amazon API Gateway | `aws-api-gateway` | `api_gateway` | `#E7157B` |
| AWS AppSync | `aws-appsync` | `appsync` | `#E7157B` |
| Amazon Athena | `aws-athena` | `athena` | `#8C4FFF` |
| Amazon Aurora | `aws-aurora` | `aurora` | `#C925D1` |
| Amazon Bedrock | `aws-bedrock` | `bedrock` | `#01A88D` |
| Client | `aws-client` | `client` | `#232F3E` |
| AWS CloudFormation | `aws-cloudformation` | `cloudformation` | `#E7157B` |
| Amazon CloudFront | `aws-cloudfront` | `cloudfront` | `#8C4FFF` |
| AWS CloudTrail | `aws-cloudtrail` | `cloudtrail` | `#E7157B` |
| Amazon CloudWatch | `aws-cloudwatch` | `cloudwatch` | `#E7157B` |
| AWS CodeBuild | `aws-codebuild` | `codebuild` | `#C925D1` |
| AWS CodePipeline | `aws-codepipeline` | `codepipeline` | `#C925D1` |
| Amazon Cognito | `aws-cognito` | `cognito` | `#DD344C` |
| AWS Direct Connect | `aws-direct-connect` | `direct_connect` | `#8C4FFF` |
| Amazon DynamoDB | `aws-dynamodb` | `dynamodb` | `#C925D1` |
| Amazon EBS | `aws-ebs` | `elastic_block_store` | `#7AA116` |
| Amazon EC2 | `aws-ec2` | `ec2` | `#ED7100` |
| Amazon ECR | `aws-ecr` | `ecr` | `#ED7100` |
| Amazon ECS | `aws-ecs` | `ecs` | `#ED7100` |
| Amazon EFS | `aws-efs` | `elastic_file_system` | `#7AA116` |
| Amazon EKS | `aws-eks` | `eks` | `#ED7100` |
| Amazon ElastiCache | `aws-elasticache` | `elasticache` | `#C925D1` |
| Elastic Load Balancing | `aws-elb` | `elastic_load_balancing` | `#8C4FFF` |
| Amazon EMR | `aws-emr` | `emr` | `#8C4FFF` |
| Amazon EventBridge | `aws-eventbridge` | `eventbridge` | `#E7157B` |
| AWS Fargate | `aws-fargate` | `fargate` | `#ED7100` |
| AWS Glue | `aws-glue` | `glue` | `#8C4FFF` |
| AWS IAM | `aws-iam` | `identity_and_access_management` | `#DD344C` |
| Internet Gateway | `aws-internet-gateway` | `internet_gateway` | `#8C4FFF` |
| Amazon Kinesis | `aws-kinesis` | `kinesis` | `#8C4FFF` |
| AWS KMS | `aws-kms` | `key_management_service` | `#DD344C` |
| AWS Lambda | `aws-lambda` | `lambda` | `#ED7100` |
| Amazon MSK | `aws-msk` | `managed_streaming_for_kafka` | `#8C4FFF` |
| NAT Gateway | `aws-nat-gateway` | `nat_gateway` | `#8C4FFF` |
| Network Load Balancer | `aws-nlb` | `network_load_balancer` | `#8C4FFF` |
| Amazon RDS | `aws-rds` | `rds` | `#C925D1` |
| Amazon Redshift | `aws-redshift` | `redshift` | `#8C4FFF` |
| Amazon Route 53 | `aws-route53` | `route_53` | `#8C4FFF` |
| Amazon S3 | `aws-s3` | `s3` | `#7AA116` |
| Amazon SageMaker | `aws-sagemaker` | `sagemaker` | `#01A88D` |
| AWS Secrets Manager | `aws-secrets-manager` | `secrets_manager` | `#DD344C` |
| AWS Shield | `aws-shield` | `shield` | `#DD344C` |
| Amazon SNS | `aws-sns` | `sns` | `#E7157B` |
| Amazon SQS | `aws-sqs` | `sqs` | `#E7157B` |
| AWS Step Functions | `aws-step-functions` | `step_functions` | `#E7157B` |
| Transit Gateway | `aws-transit-gateway` | `transit_gateway` | `#8C4FFF` |
| Users | `aws-users` | `users` | `#232F3E` |
| Amazon VPC | `aws-vpc` | `vpc` | `#8C4FFF` |
| VPC Endpoint | `aws-vpc-endpoint` | `endpoint` | `#8C4FFF` |
| AWS WAF | `aws-waf` | `waf` | `#DD344C` |

## Azure — `azure-*` (28)

Image icons, not stencils: the style carries a relative path to an SVG that draw.io ships. Fixed colour — `fill` does not apply.

| Service | Key | draw.io name | Fill |
| --- | --- | --- | --- |
| Container Registry | `azure-acr` | `containers/Container_Registries.svg` | — |
| AI Search | `azure-ai-search` | `ai_machine_learning/Serverless_Search.svg` | — |
| Azure Kubernetes Service | `azure-aks` | `compute/Kubernetes_Services.svg` | — |
| API Management | `azure-api-management` | `app_services/API_Management_Services.svg` | — |
| Application Gateway | `azure-app-gateway` | `networking/Application_Gateway_Containers.svg` | — |
| Application Insights | `azure-app-insights` | `devops/Application_Insights.svg` | — |
| App Service | `azure-app-service` | `app_services/App_Service_Certificates.svg` | — |
| Blob Storage | `azure-blob` | `general/Blob_Block.svg` | — |
| Container Apps | `azure-container-apps` | `networking/Application_Gateway_Containers.svg` | — |
| Cosmos DB | `azure-cosmos-db` | `databases/Azure_Cosmos_DB.svg` | — |
| Data Factory | `azure-data-factory` | `databases/Data_Factory.svg` | — |
| Microsoft Entra ID | `azure-entra-id` | `identity/Entra_Connect.svg` | — |
| Event Grid | `azure-event-grid` | `integration/Event_Grid_Domains.svg` | — |
| Event Hubs | `azure-event-hubs` | `analytics/Event_Hub_Clusters.svg` | — |
| Front Door | `azure-front-door` | `networking/Front_Doors.svg` | — |
| Azure Functions | `azure-functions` | `compute/Function_Apps.svg` | — |
| Key Vault | `azure-key-vault` | `security/Key_Vaults.svg` | — |
| Load Balancer | `azure-load-balancer` | `networking/Load_Balancer_Hub.svg` | — |
| Logic Apps | `azure-logic-apps` | `integration/Logic_Apps.svg` | — |
| Azure Monitor | `azure-monitor` | `management_governance/Monitor.svg` | — |
| Azure OpenAI | `azure-openai` | `ai_machine_learning/Azure_OpenAI.svg` | — |
| Azure PostgreSQL | `azure-postgresql` | `databases/Azure_Database_PostgreSQL_Server.svg` | — |
| Azure Cache for Redis | `azure-redis` | `databases/Cache_Redis.svg` | — |
| Service Bus | `azure-service-bus` | `general/Service_Bus.svg` | — |
| Azure SQL Database | `azure-sql` | `databases/Azure_Database_MySQL_Server.svg` | — |
| Synapse Analytics | `azure-synapse` | `analytics/Azure_Synapse_Analytics.svg` | — |
| Virtual Machine | `azure-vm` | `compute/Virtual_Machine.svg` | — |
| Virtual Network | `azure-vnet` | `networking/Virtual_Network_Gateways.svg` | — |

## Google Cloud — `gcp-*` (18)

Mostly the `gcp3` set. A few products only exist in the older `gcp2` set and carry a fully qualified name; both render identically.

| Service | Key | draw.io name | Fill |
| --- | --- | --- | --- |
| AlloyDB | `gcp-alloydb` | `alloydb` | `#4285F4` |
| Anthos | `gcp-anthos` | `anthos` | `#4285F4` |
| Apigee | `gcp-apigee` | `apigee` | `#4285F4` |
| App Engine | `gcp-app-engine` | `mxgraph.gcp2.app_engine` | `#4285F4` |
| BigQuery | `gcp-bigquery` | `bigquery` | `#4285F4` |
| Cloud Bigtable | `gcp-bigtable` | `mxgraph.gcp2.cloud_bigtable` | `#4285F4` |
| Cloud Functions | `gcp-cloud-functions` | `mxgraph.gcp2.cloud_functions` | `#4285F4` |
| Cloud Run | `gcp-cloud-run` | `cloudrun` | `#4285F4` |
| Cloud SQL | `gcp-cloud-sql` | `cloudsql` | `#4285F4` |
| Cloud Storage | `gcp-cloud-storage` | `cloud_storage` | `#4285F4` |
| Compute Engine | `gcp-compute-engine` | `computeengine` | `#4285F4` |
| Dataflow | `gcp-dataflow` | `mxgraph.gcp2.cloud_dataflow` | `#4285F4` |
| Dataproc | `gcp-dataproc` | `mxgraph.gcp2.cloud_dataproc` | `#4285F4` |
| Firestore | `gcp-firestore` | `mxgraph.gcp2.cloud_firestore` | `#4285F4` |
| Google Kubernetes Engine | `gcp-gke` | `gke` | `#4285F4` |
| Pub/Sub | `gcp-pubsub` | `mxgraph.gcp2.cloud_pubsub` | `#4285F4` |
| Cloud Spanner | `gcp-spanner` | `cloudspanner` | `#4285F4` |
| Vertex AI | `gcp-vertex-ai` | `vertexai` | `#4285F4` |

## Kubernetes — `k8s-*` (16)

Rendered through the `icon2` badge wrapper, which draws the white resource glyph on a blue tile. Names are Kubernetes' own short codes.

| Service | Key | draw.io name | Fill |
| --- | --- | --- | --- |
| API Server | `k8s-api` | `api` | `#2875E2` |
| ConfigMap | `k8s-configmap` | `cm` | `#2875E2` |
| CronJob | `k8s-cronjob` | `cronjob` | `#2875E2` |
| DaemonSet | `k8s-daemonset` | `ds` | `#2875E2` |
| Deployment | `k8s-deployment` | `deploy` | `#2875E2` |
| Ingress | `k8s-ingress` | `ing` | `#2875E2` |
| Job | `k8s-job` | `job` | `#2875E2` |
| Namespace | `k8s-namespace` | `ns` | `#2875E2` |
| Node | `k8s-node` | `node` | `#2875E2` |
| Pod | `k8s-pod` | `pod` | `#2875E2` |
| PersistentVolume | `k8s-pv` | `pv` | `#2875E2` |
| PersistentVolumeClaim | `k8s-pvc` | `pvc` | `#2875E2` |
| ReplicaSet | `k8s-replicaset` | `rs` | `#2875E2` |
| Secret | `k8s-secret` | `secret` | `#2875E2` |
| Service | `k8s-service` | `svc` | `#2875E2` |
| StatefulSet | `k8s-statefulset` | `sts` | `#2875E2` |

## Cisco — `cisco-*` (6)

Monochrome network-equipment stencils from the `cisco19` set.

| Service | Key | draw.io name | Fill |
| --- | --- | --- | --- |
| Firewall | `cisco-firewall` | `firewall` | — |
| Load Balancer | `cisco-load-balancer` | `load_balancer` | — |
| Router | `cisco-router` | `router` | — |
| Switch | `cisco-switch` | `l3_switch` | — |
| VPN Concentrator | `cisco-vpn-gateway` | `vpn_concentrator` | — |
| Wireless AP | `cisco-wireless-ap` | `wireless_access_point` | — |

## Generic network — `net-*` (9)

Generic network shapes. Use these when the diagram is vendor-neutral.

| Service | Key | draw.io name | Fill |
| --- | --- | --- | --- |
| Cloud | `net-cloud` | `cloud` | — |
| Firewall | `net-firewall` | `firewall` | — |
| Laptop | `net-laptop` | `laptop` | — |
| Mobile | `net-mobile` | `mobile` | — |
| Router | `net-router` | `router` | — |
| Server | `net-server` | `server` | — |
| Storage | `net-storage` | `storage` | — |
| Switch | `net-switch` | `switch` | — |
| User | `net-user` | `users` | — |

