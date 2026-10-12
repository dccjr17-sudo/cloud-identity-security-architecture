# Validation plan and evidence status

**Current status:** design review and offline checks only. No live tenant, Azure subscription, AWS account, GitHub OIDC trust, or cloud monitor was configured for Project 6. Expected results below are acceptance criteria, not observed cloud results.

| Test | Expected result | Required future evidence |
| --- | --- | --- |
| Catalog runtime reads intended blob | Allowed | Token identity, container scope, successful API call |
| Runtime writes blob or reads other container | Denied | Sanitized failed API calls; inherited grants reviewed |
| Azure Reader reads blob contents without data role | Denied through Entra path | Management role plus data-call result; shared-key paths assessed |
| Azure CI deploys catalog app | Allowed | OIDC claims, service principal, scoped deployment result |
| Azure CI creates RBAC assignment | Denied | Negative API result and complete effective-grant inventory |
| Approved GitHub repository / production environment | AWS STS role session issued | Actual issuer, aud, sub, role/session metadata |
| Wrong repository, environment, or audience | STS denied | Negative assumption attempts |
| Unapproved branch using production environment | Blocked by GitHub environment policy | Environment protection settings and rejected deployment |
| Uploader writes reports/artifact.json | Allowed | Actual PutObject result and CloudTrail data event |
| Uploader reads, deletes, lists, or writes outside prefix | Denied in isolated role configuration | Negative calls and all applicable policy documents |
| Reader gets report or lists reports/ prefix | Allowed | GetObject/ListObjectsV2 results |
| Reader writes or lists unrestricted bucket | Denied in isolated permission-set configuration | Negative calls |
| Entra user/group provisioning | Expected identities synchronize | SCIM events and Identity Center records |
| Unassigned workforce user | No AWS account access | Portal result and account assignment inventory |
| Leaver containment | New sign-in blocked; existing session handling measured | Cross-system timeline and actual session tests |
| Emergency access during IdP outage | Documented recovery succeeds and alerts fire | Controlled drill, alert, approval and post-use review |
| S3 object read logging | Read appears in configured data-event trail | Event selector and sample event |

Run `python validation/check_examples.py` for local JSON, trust-boundary, action/resource/prefix, and diagram checks. The evaluator supports the small Allow/StringLike subset used here, with explicit default refusal. It does not implement the full AWS policy engine, resource policies, permissions boundaries, SCPs, session policies, KMS, or Azure RBAC. Its allow/deny checks describe only these isolated examples.

Before deploying: substitute placeholders; obtain resource owners' approval; validate Azure role scopes and Azure federation claims; run AWS ValidatePolicy; confirm effective grants and logging; execute negative tests; record rollback and recovery procedures. Any live deployment requires its own authorized sandbox scope.

