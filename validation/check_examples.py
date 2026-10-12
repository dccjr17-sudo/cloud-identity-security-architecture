"""Offline checks for these exact examples, not a cloud authorization engine."""
import fnmatch
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
POLICIES = ROOT / 'policies'
passed = []


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    passed.append(name)


def load(name):
    return json.loads((POLICIES / name).read_text(encoding='utf-8-sig'))


def listify(value):
    return value if isinstance(value, list) else [value]


def example_allows(policy, action, resource, prefix=None):
    # Supports only this project's Allow statements and s3:prefix StringLike.
    # Unknown constructs fail rather than being silently treated as allowed.
    result = False
    for statement in policy['Statement']:
        if statement['Effect'] != 'Allow':
            raise ValueError('Unsupported effect for this isolated example check')
        if set(statement) - {'Sid', 'Effect', 'Action', 'Resource', 'Condition'}:
            raise ValueError('Unsupported statement construct')
        condition = statement.get('Condition')
        if condition and (set(condition) != {'StringLike'} or
                          set(condition['StringLike']) != {'s3:prefix'}):
            raise ValueError('Unsupported condition')
        actions = listify(statement['Action'])
        resources = listify(statement['Resource'])
        if action not in actions or not any(fnmatch.fnmatchcase(resource, r) for r in resources):
            continue
        if condition:
            if prefix is None or not any(fnmatch.fnmatchcase(prefix, p) for p in
                                         listify(condition['StringLike']['s3:prefix'])):
                continue
        result = True
    return result


trust = load('aws-github-trust.json')['Statement']
check('One AWS trust statement', len(trust) == 1)
statement = trust[0]
claims = statement['Condition']['StringEquals']
check('Exact OIDC provider and AssumeRoleWithWebIdentity action',
      statement['Principal'] == {'Federated': 'arn:aws:iam::111122223333:oidc-provider/token.actions.githubusercontent.com'}
      and statement['Action'] == 'sts:AssumeRoleWithWebIdentity')
expected = {'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com',
            'token.actions.githubusercontent.com:sub': 'repo:northstar-example/report-publisher:environment:production'}
check('AWS audience and subject are exact', claims == expected and
      not any('*' in v or '?' in v for v in claims.values()))
for label, aud, sub in [
    ('Approved AWS claims', 'sts.amazonaws.com', expected['token.actions.githubusercontent.com:sub']),
    ('Wrong audience', 'other-service', expected['token.actions.githubusercontent.com:sub']),
    ('Wrong repository', 'sts.amazonaws.com', 'repo:other/repo:environment:production'),
    ('Wrong environment', 'sts.amazonaws.com', 'repo:northstar-example/report-publisher:environment:development'),
]:
    matches = aud == expected['token.actions.githubusercontent.com:aud'] and sub == expected['token.actions.githubusercontent.com:sub']
    check(label, matches == (label == 'Approved AWS claims'))

federation = load('azure-github-federated-credential.json')
check('Azure exact issuer, subject, audience',
      federation['issuer'] == 'https://token.actions.githubusercontent.com' and
      federation['subject'] == 'repo:northstar-example/catalog-api:environment:production' and
      federation['audiences'] == ['api://AzureADTokenExchange'])
azure_plan = load('azure-role-assignment-plan.json')['assignments']
check('Azure runtime role scoped to catalog container',
      azure_plan[0]['roleName'] == 'Storage Blob Data Reader' and
      azure_plan[0]['scope'].endswith('/blobServices/default/containers/catalog-published'))
check('Azure deployment role scoped to individual app',
      azure_plan[1]['roleName'] == 'Website Contributor' and
      azure_plan[1]['scope'].endswith('/Microsoft.Web/sites/EXAMPLE-CATALOG-APP'))

uploader = load('aws-report-uploader.json')
reader = load('aws-report-reader.json')
bucket = 'arn:aws:s3:::northstar-example-reports-prod'
object_arn = bucket + '/reports/artifact.json'
checks = [
    ('Uploader can put intended object', uploader, 's3:PutObject', object_arn, None, True),
    ('Uploader cannot get object', uploader, 's3:GetObject', object_arn, None, False),
    ('Uploader cannot delete object', uploader, 's3:DeleteObject', object_arn, None, False),
    ('Uploader cannot list bucket', uploader, 's3:ListBucket', bucket, 'reports/', False),
    ('Uploader cannot put outside prefix', uploader, 's3:PutObject', bucket + '/private/key', None, False),
    ('Uploader cannot write another bucket', uploader, 's3:PutObject', 'arn:aws:s3:::other/reports/key', None, False),
    ('Reader can read intended object', reader, 's3:GetObject', object_arn, None, True),
    ('Reader can list reports prefix', reader, 's3:ListBucket', bucket, 'reports/', True),
    ('Reader can list descendant prefix', reader, 's3:ListBucket', bucket, 'reports/2026/', True),
    ('Reader cannot list full bucket', reader, 's3:ListBucket', bucket, '', False),
    ('Reader cannot list lookalike prefix', reader, 's3:ListBucket', bucket, 'reports-private/', False),
    ('Reader cannot write', reader, 's3:PutObject', object_arn, None, False),
    ('Reader cannot delete', reader, 's3:DeleteObject', object_arn, None, False),
    ('Reader cannot read outside prefix', reader, 's3:GetObject', bucket + '/private/key', None, False),
]
for name, policy, action, resource, prefix, expected_result in checks:
    check(name, example_allows(policy, action, resource, prefix) == expected_result)
for name, policy in [('Uploader', uploader), ('Reader', reader)]:
    check(name + ' has no unrestricted action or resource', all(
        '*' not in listify(s['Action']) and '*' not in listify(s['Resource'])
        for s in policy['Statement']))

diagram = ROOT / 'diagrams' / 'zero-trust-architecture.svg'
check('SVG parses and declares title and description',
      ET.parse(diagram).getroot().find('{http://www.w3.org/2000/svg}title') is not None and
      ET.parse(diagram).getroot().find('{http://www.w3.org/2000/svg}desc') is not None)
check('Mermaid source includes both cloud identity flows',
      all(word in (ROOT / 'diagrams' / 'zero-trust-architecture.mmd').read_text(encoding='utf-8-sig')
          for word in ['Entra', 'Identity Center', 'OIDC', 'SCIM', 'monitoring']))
output = '\n'.join('PASS: ' + name for name in passed)
output += f'\n\n{len(passed)} offline checks passed. No cloud resources or effective authorization tested.\n'
print(output)
