# Security Policy

## Secrets

Never commit Azure keys, connection strings, access tokens, private regulation files, or a populated `.env`. Use `.env.example` only as a list of variable names. Production deployments should prefer Azure Managed Identity and RBAC over long-lived keys.

If a credential is committed, revoke or rotate it immediately. Removing the line in a later commit does not remove it from Git history.

## Reporting

Do not open a public issue containing a credential, private policy document, personal data, or an exploitable vulnerability. Contact the repository maintainer through a private channel and include only the minimum information needed to reproduce the problem.

