# Setting up AWS

The agent runs on AWS Lambda ([ADR-001](../adr/ADR-001-compute-platform.md)). You
need an AWS account and a set of credentials that Terraform (and CI) can use to
create and update resources.

> **Cost:** the resources we use (Lambda, CloudWatch Logs, Function URL) sit in the
> always-free tier for a personal bot. An account still requires a credit card, and
> anything outside the free tier would bill normally.

## 1. Create an AWS account

1. Go to <https://aws.amazon.com> → **Create an AWS Account**.
2. Provide email, password, a credit card, and verify your phone number.
3. Choose the **Basic (free)** support plan.

## 2. Secure the root user

The email/password you just made is the **root** user — very powerful. Protect it:

1. Sign in to the [IAM console](https://console.aws.amazon.com/iam/).
2. Enable **MFA** on the root user.
3. Don't use root for day-to-day work — create a deploy user next.

## 3. Create a deploy user with access keys

Terraform and CI authenticate with an IAM user's access key (long-lived credentials).

1. IAM → **Users** → **Create user** (e.g. `discord-agent-deploy`). Do **not** give
   it console access.
2. Attach permissions. Simplest to start: **AdministratorAccess**. To scope it down
   later, this project only needs Lambda, IAM (role/policy management), and
   CloudWatch Logs.
3. Open the user → **Security credentials** → **Create access key** →
   **Command Line Interface (CLI)**. Copy the **Access key ID** and **Secret access
   key** (shown once).

## 4. Configure the AWS CLI locally

Install the AWS CLI, then:

```bash
aws configure
# AWS Access Key ID:     <your access key id>
# AWS Secret Access Key: <your secret access key>
# Default region name:   us-west-2      # match your Neon region / aws_region
# Default output format:  json
```

Verify:

```bash
aws sts get-caller-identity
```

You should see your account ID and user ARN.

## Where these credentials go

- **Locally:** `aws configure` stores them in `~/.aws/credentials` (outside this
  repo) — Terraform uses them for `terraform apply`.
- **CI:** the same access key ID / secret go into **GitHub Actions secrets**
  (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`) for code deploys —
  set these during the [deploy](deploy.md) step. They are **not** stored in the repo.
