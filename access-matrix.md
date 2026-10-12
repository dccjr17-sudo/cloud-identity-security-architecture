# Access matrix

All names and scopes are fictional. These are proposed grants, not current tenant access. Entra directory roles and Azure resource roles are different authorization systems.

| Identity | Authentication | Proposed permission | Scope | Approval and lifecycle |
| --- | --- | --- | --- | --- |
| Retail employees | Entra SSO, MFA, device checks | Application-defined catalog viewer role | Catalog API only | Business owner approves group assignment; remove on exit |
| Development engineers | Entra workforce account | Azure Reader; development deployment role separately reviewed | Development resource group | No inherited production write role |
| Production operators | Separate Entra admin account | Azure Reader standing; eligible Website Contributor | Individual production App Service | Proposed PIM activation up to 60 minutes with approval and phishing-resistant authentication |
| Catalog runtime | System-assigned managed identity | Storage Blob Data Reader | One `catalog-published` blob container | Resource-bound identity; no storage management role |
| Azure CI deployment | GitHub OIDC federated app identity | Website Contributor | Individual catalog App Service | Protected `production` environment; deployment approval; no role-assignment grant |
| AWS report readers | Entra SAML to IAM Identity Center | Custom permission set: GetObject on `reports/*`, prefix-constrained ListBucket | Reporting bucket in production account | Group assignment by owner; proposed one-hour AWS sessions |
| AWS report Lambda | Lambda service identity / execution role | Same narrow report read policy plus separately scoped logging | Reporting prefix and its own log group | Separate execution role per environment |
| AWS artifact uploader | GitHub OIDC to AWS STS | PutObject on `reports/*` only | One reporting bucket | Exact repository/environment trust; proposed 15-minute role session |
| Security analysts | Entra administrative account and federated AWS session | Entra Security Reader; separately reviewed Azure log-read grants and AWS audit permission set | Security tooling and log stores | No production deployment or IAM policy modification |
| Azure access administrators | Separate Entra admin account | Eligible narrowly scoped role-assignment administration | Production resource group | Independent approval; delegation conditions reviewed before deployment |
| Emergency Azure identities | Two cloud-only Entra accounts with resilient credentials | Global Administrator for tenant recovery | Entra tenant; Azure recovery authorization reviewed separately | Monitored emergency use; independent custody; no daily use |
| Emergency AWS recovery | Dedicated recovery procedure including root protection | Explicit account recovery responsibilities | Each AWS account | Hardware MFA, controlled custody, immediate alert and post-use review |

Website Contributor can deploy or execute application code. That code can use the app's managed identity to read catalog data. The deployer therefore has an indirect path to that data even without an explicit blob role. Treat production code deployment as data-sensitive authorization.

Directory readers do not automatically have cloud resource access. Azure Reader is a management-plane permission and does not grant blob contents. AWS permission sets create account-specific role permissions; Entra groups alone do not authorize AWS API calls.

Group names: `NS-Catalog-Viewers`, `NS-Dev-Engineers`, `NS-Prod-Operators`, `NS-AWS-Report-Readers`, and `NS-Security-Analysts`. These groups require owners, review cadence, and approval records. Keep production and development memberships separate; avoid nested-group assumptions across SCIM synchronization.

