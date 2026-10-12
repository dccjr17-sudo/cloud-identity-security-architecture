# Example policies and boundaries

These are standalone illustrative policy documents, not deployment scripts. Account `111122223333`, organization `northstar-example`, repositories, bucket, and environment names are fictional placeholders. Never attach these examples to a real account without replacing and independently reviewing them.

| File | Purpose | Does not supply |
| --- | --- | --- |
| aws-github-trust.json | Exact GitHub OIDC repository/environment trust with AWS audience | OIDC provider creation, permissions, GitHub protections, session-duration setting |
| aws-report-uploader.json | Single PutObject permission under reports prefix | Read/list/delete, IAM administration, KMS or multipart permissions |
| aws-report-reader.json | Prefix-scoped object read and listing | Writes/deletes, bucket-wide listing, KMS permissions |
| azure-github-federated-credential.json | Entra external workload trust with token-exchange audience | App registration, service principal, role assignment, deployment workflow |
| azure-role-assignment-plan.json | Named roles and resource/container scope examples | Valid subscription/principal IDs or an executable deployment template |

Attach the uploader permission document to the CI role whose trust document is supplied. The reader permission document can be the custom policy for the human Identity Center permission set or part of a Lambda execution role. The Lambda service trust and logging policy require separate environment-specific configuration; the GitHub trust is not the Lambda trust.

Use the Azure federated-credential document on the dedicated deployment app registration, then assign its service principal the resource-scoped role from the matrix. The catalog runtime identity is a separate managed identity with Storage Blob Data Reader at the container scope. Authentication trust does not grant those roles.

These policy permissions are intentionally incomplete for broad deployment tools. Use direct, minimal API operations for the planned upload; generic synchronization tools may request list, delete, or multipart privileges. Reject those extras unless the workload requirement is explicitly revised.

AWS effective permission must consider every applicable policy. A missing Allow in this one document does not neutralize an Allow elsewhere. Bucket policies, boundaries, SCPs, session policies, and encryption keys must be reviewed. Azure effective access similarly includes inherited role assignments and alternative storage authorization paths.

Future verification: AWS IAM Access Analyzer ValidatePolicy and appropriate policy simulation, followed by actual sandbox calls. Local checks model only the action/resource/prefix subset of these examples; they are not the AWS IAM evaluator. Entra federation must be tested against actual GitHub-issued claims. No workflow or credential is installed here.

