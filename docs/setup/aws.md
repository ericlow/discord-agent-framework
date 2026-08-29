# Setting up AWS

The agent runs on AWS Lambda ([ADR-001](../adr/ADR-001-compute-platform.md)). You
need an AWS account and a set of credentials that Terraform (and CI) can use to
create and update resources.

> **Cost:** the resources we use (Lambda, CloudWatch Logs, Function URL) sit in the
> always-free tier for a personal bot. An account still requires a credit card, and
> anything outside the free tier would bill normally.

## 1. Create an AWS account

**Already have an AWS account?** Skip this section — sign in and go straight to
[step 3](#3-create-a-deploy-user-with-access-keys) to create the deploy user.

1. Go to <https://aws.amazon.com> → **Create an AWS Account**.
2. Provide email, password, a credit card, and verify your phone number.
3. Choose the **Basic (free)** support plan.

> AWS accounts are tied to an email address, and each address can back only one
> account. If you're out of fresh addresses, reuse an existing account rather than
> signing up again.

## 2. Secure the root user

The email/password you just made is the **root** user — very powerful. Protect it:

1. Sign in to the [IAM console](https://console.aws.amazon.com/iam/).
2. Enable **MFA** on the root user.
3. Don't use root for day-to-day work — create a deploy user next.

## 3. Create a deploy user with access keys

Terraform and CI authenticate with an IAM user's access key (long-lived credentials).

1. IAM → **Users** → **Create user**, name it `discord-agent-deploy`. On the first
   screen, **leave "Provide user access to the AWS Management Console" unchecked** —
   this user is for the CLI and CI only, so it needs no console password.
2. **Set permissions** → **Attach policies directly**. Simplest to start:
   **AdministratorAccess**. To scope it down later, this project only needs Lambda,
   IAM (role/policy management), and CloudWatch Logs. Create the user.
3. Open the user → **Security credentials** tab → **Access keys** → **Create access
   key**. Choose **Command Line Interface (CLI)**. AWS will show an "alternatives
   recommended" notice and ask you to tick a confirmation box — this is expected;
   we use a long-lived access key on purpose so Terraform and CI authenticate the
   same way. The optional description tag can be left blank.
4. On the final screen, copy the **Access key ID** and **Secret access key**. The
   secret is shown **once** — copy both now (or **Download .csv file**).

> **Keep the secret secret.** Treat the secret access key like a password: don't
> paste it into chat, commit it, or share it. If it's ever exposed, delete that key
> (IAM → the user → Security credentials) and create a new one.

## 4. Configure the AWS CLI locally

Install the AWS CLI, then:

```bash
aws configure
# AWS Access Key ID:     <your access key id>
# AWS Secret Access Key: <your secret access key>
# Default region name:   us-west-2      # must match aws_region in infra/terraform.tfvars
# Default output format:  json
```

The region here should match `aws_region` in `infra/terraform.tfvars` (Terraform
deploys there regardless, but matching keeps CLI inspection pointed at the same
place). Running `aws configure` again overwrites any older credentials.

Verify:

```bash
aws sts get-caller-identity
```

You should see your account ID and the `discord-agent-deploy` user ARN — for
example `arn:aws:iam::<account-id>:user/discord-agent-deploy`.

## Where these credentials go

- **Locally:** `aws configure` stores them in `~/.aws/credentials` (outside this
  repo) — Terraform uses them for `terraform apply`.
- **CI:** the same access key ID / secret go into **GitHub Actions secrets**
  (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`) for code deploys —
  set these during the [deploy](deploy.md) step. They are **not** stored in the repo.
