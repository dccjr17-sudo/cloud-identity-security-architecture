# Northstar Retail: cloud identity security design

Prepared October 12, 2026. Fictional architecture; no controls deployed. Local policy checks are separate from live security validation.

## 1. Business requirements and boundaries

Northstar publishes a product catalog from Azure and distributes generated business reports from AWS. Employees need catalog access; a small analytics group needs report access. Operators must deploy and recover services without standing broad administrative access. Pipelines must avoid stored cloud access keys. Every production grant needs a purpose, owner, scope, expiry or review cadence, and an auditable change record.

Use separate Azure subscriptions and AWS accounts for development and production. Place audit collection in a separately administered security boundary. This separation is a proposed design choice, not proof that cross-environment access has been prevented. Enumerate inherited Azure grants, AWS resource policies, permission sets, trust relationships, and organization policies before implementation.

## 2. Human authentication and authorization

Entra is the workforce identity source. A pilot Conditional Access policy requires MFA and compliant managed devices for cloud administration. Privileged sign-in uses phishing-resistant authentication and separate administrative accounts. Introduce policies in report-only mode, test pilot users and recovery identities, then enforce in stages. Conditional Access, device compliance, risk signals, PIM, and access reviews have licensing and service prerequisites that must be confirmed against actual subscriptions.

The catalog application validates token issuer, audience, signature, and expiry and enforces its own viewer role. A successful Entra sign-in alone is not an application authorization decision. Azure RBAC governs Azure resources; Entra directory roles govern directory administration. These controls must be reviewed independently. [Entra role guidance](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/best-practices), [Azure role assignments](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-assignments).

For AWS, configure Entra SAML federation with IAM Identity Center and SCIM provisioning of designated users and groups. SAML authenticates the workforce session; SCIM synchronizes identities; Identity Center account assignments and permission sets determine access. Provisioning alone grants no AWS permission set. Monitor synchronization failures and token expiry, keep its SCIM bearer token in an approved secret store, and plan rotation. [AWS Entra integration](https://docs.aws.amazon.com/singlesignon/latest/userguide/idp-microsoft-entra.html).

A one-hour Identity Center session is a Northstar proposal. Entra policy evaluation at sign-in does not imply continuous re-evaluation of every AWS API call. Disablement, assignment removal, provisioning latency, and previously issued cloud sessions require separate incident handling and tests.

## 3. Azure resource and workload access

The catalog API uses a system-assigned managed identity, selected because one app owns its lifecycle. Give it Storage Blob Data Reader on the `catalog-published` container only. Do not grant subscription Contributor, storage management, or key-listing permissions to the runtime. Use Entra authorization for storage, disable shared-key access where compatible, and use private endpoints and tested DNS/routing for data access. Identity authorization and network reachability are both required.

Production operators have standing Reader and an eligible, resource-scoped deployment role. Northstar proposes independent approval, a ticket, and a 60-minute activation window. A deployment role can execute code with the runtime identity's privileges, so its scope does not eliminate indirect catalog-data access. Review this path explicitly. [Managed identity boundaries](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/managed-identity-best-practice-recommendations), [Blob role definition](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/storage).

CI uses an Entra app identity with an exact GitHub issuer, subject, and token-exchange audience. The federation entry identifies the permitted workflow context; it does not grant resource rights. Assign Website Contributor separately at the catalog app scope. This built-in role also permits app management, including settings changes and deletion within scope; it is a reviewed convenience tradeoff, not a deploy-only custom role. A future implementation should trace required deployment operations and consider a narrower custom role. Keep the deployment identity separate from the runtime managed identity and from identities that administer RBAC. [Entra federated credentials](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-create-trust), [Website Contributor definition](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/web-and-mobile#website-contributor).

## 4. AWS workload identities and permissions

Use IAM roles and temporary credentials for the reporting Lambda and CI pipeline. The Lambda execution-role trust names the Lambda service, while its permission policy reads only one reporting prefix. Its logging permissions must name the actual precreated log group; they are intentionally outside the supplied S3 policy. No IAM user access key is proposed. [AWS temporary-credential guidance](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html).

The uploader trust policy permits only `sts:AssumeRoleWithWebIdentity` from the account's GitHub OIDC provider, with exact `aud` and `sub` values. The example uses a protected `production` GitHub environment. Because its subject identifies the environment rather than a branch, configure deployment branch restrictions and required reviewers in GitHub. The trust policy alone does not enforce a particular branch. Forks, pull requests, other repositories, and other environments must fail the future trust tests. [AWS GitHub OIDC guidance](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html).

The uploader can PutObject only under `reports/*`; it cannot list, read, delete, change bucket policies, or manage IAM through this policy. It can overwrite existing objects in that prefix, which is a material risk. Use versioning, immutable artifact names, integrity checks, and independently controlled retention. The example assumes single-request uploads and bucket-managed SSE-S3 encryption. SSE-KMS or multipart workflows require a reviewed policy extension; do not infer that this example covers them.

The reader receives GetObject under the same prefix and ListBucket only when the requested prefix matches `reports/` or its descendants. This limits listing as well as object access. The wildcard suffix selects keys inside an intended namespace; it is not unrestricted account access. These identity-policy omissions are implicit denies only in isolation: additional identity grants, resource policies, boundaries, session policies, service control policies, and explicit denies affect effective authorization. [S3 prefix restrictions](https://docs.aws.amazon.com/AmazonS3/latest/userguide/amazon-s3-policy-keys.html).

## 5. Zero Trust decisions and threats

| Threat or failure | Proposed control | Residual risk / validation needed |
| --- | --- | --- |
| Stolen workforce credential | Phishing-resistant privileged sign-in; compliant device gate | Token theft and prior AWS sessions still need containment |
| Excessive administrator grant | Narrow scope, time-limited activation, independent approval | Inheritance and code-to-runtime privilege paths require review |
| Compromised CI workflow | Exact OIDC trust, protected environment, reviewed changes | Approved malicious code can still misuse its intended scope |
| Runtime compromise | Per-workload role, read-only data scope, network boundaries | Authorized data can still be read and exfiltrated by compromised code |
| Mover keeps old access | Remove old grant, verify, add new grant, verify | Multi-system changes are not atomic; failed steps require reconciliation |
| Leaver retains session | Disable identity, remove grants, assess session invalidation | SCIM and credential expiry may delay containment |
| Attacker tampers with evidence | Separate log administration and retention; alert on log control changes | Monitoring and retention have not been configured here |
| Identity provider outage | Independently controlled recovery identities and rehearsed runbooks | Recovery paths are privileged and must be monitored |

No network location or successful login is sufficient to trust a request. Validate identity and token context, enforce the resource permission, minimize accessible data, and instrument the operation. The diagram's arrows show distinct identity paths; log arrows represent telemetry rather than permission grants.

## 6. Lifecycle and emergency operations

Joiner: verify the HR event, obtain business-owner approval, add the minimum group, confirm downstream provisioning and app/account assignment. Mover: compare actual grants to the new role, remove old entitlements, verify removal, add approved new entitlements, and investigate partial results. Leaver: disable sign-in, remove memberships and assignments, rotate any nonfederated credentials, address active sessions, and verify downstream denial. The earlier IAM Automation project is an example of selected steps, not proof that this architecture's lifecycle is operational.

For Azure tenant recovery, design two cloud-only emergency accounts with credentials that avoid the normal administrative failure path. Document any policy exceptions narrowly; alert on every use and rehearse recovery. Global Administrator is not an ordinary workload role, and Azure subscription recovery permissions need a separate decision. For AWS, protect account root credentials with hardware MFA and controlled custody, avoid root daily use and access keys, and document recovery ownership. Independent reviewers must approve any persistent recovery authorization before deployment.

An incident response runbook must distinguish stopping new token issuance from invalidating or restricting already issued sessions. Entra workforce disablement alone is not an immediate AWS session kill switch. AWS session containment must use the relevant current service procedure and verified policy effect. Managed-identity authorization changes may also be subject to caching. Treat containment latency as a measured acceptance criterion, not a guaranteed property.

## 7. Monitoring, review, and implementation order

Collect Entra sign-in/audit/provisioning events, Azure Activity Logs and relevant resource diagnostics, AWS CloudTrail management events, and explicitly configured S3 object data events. Default management logging is not sufficient evidence of object reads. Alert on privileged activation, role/trust changes, recovery sign-in, provisioning failures, unusual data access, and logging changes. Assign an alert owner and response playbook. Cost, retention, and data-event volume need budgeting.

Monthly review: workforce production memberships, access-administrator eligibility, inactive identities, and workload owners. Quarterly review: federation trust, CI environment protection, resource-policy findings, root/emergency access drills, and session-containment latency. These cadences are scenario choices.

Implementation order: inventory inherited access and licensing; create isolated sandboxes; configure logs; pilot workforce authentication; establish narrow resource grants; implement federation and workloads; run positive and negative tests; rehearse rollback and recovery; obtain owner approval before production. Avoid blocking the final emergency path during rollout.

## 8. Acceptance and evidence

The [validation plan](validation/validation-plan.md) defines expected results. Local checks can show that example JSON expresses chosen boundaries; they cannot prove cloud denial, correct RBAC deployment, end-to-end SSO, network isolation, or incident recovery. Record actual timestamps, effective identities, request scope, allow/deny results, and sanitized evidence in a future lab. No production readiness or compliance certification is claimed.

