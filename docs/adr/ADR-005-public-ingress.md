# ADR-005: Public ingress via API Gateway HTTP API

_Status: accepted_
_Date: 2026-08-29_

**We will expose the Lambda to Discord through an API Gateway HTTP API rather than a
Lambda Function URL, because this AWS account has Lambda Block Public Access enabled
at the account level, which makes Function URLs return 403 regardless of their
resource policy.**

## Context

[ADR-001](ADR-001-compute-platform.md) runs the agent on Lambda behind an HTTP
interactions endpoint. The original infra used a **Lambda Function URL**
(`authorization_type = NONE` plus a resource-based `lambda:InvokeFunctionUrl`
permission for principal `*`) — the simplest, free-forever way to give a function a
public HTTPS address.

During the first real deploy it returned **HTTP 403 (`AccessDeniedException`) at the
URL layer, before the function ran** (zero CloudWatch invocations), for every request
including Discord's verification PING. We verified the function itself is healthy (a
direct `lambda invoke` returns the handler's normal `401 invalid request signature`),
the URL's `AuthType` is `NONE`, the resource policy is correct (`principal: "*"`,
`lambda:InvokeFunctionUrl`, condition `lambda:FunctionUrlAuthType = NONE`), the
account is **not** in an AWS Organization (no SCP), and the 403 persisted across a
full 4-minute propagation window and a brand-new URL created seconds before the test.

Root cause: the account has **Lambda Block Public Access** turned on at the account
level, which blocks public Function URLs irrespective of the resource policy. The
installed AWS CLI is too old to expose the toggle to disable it. This is the same
issue a sibling project (Health-Insurance-News-Agent) hit and worked around the same
way; its Terraform carries the note *"Lambda Function URLs are blocked by the
account's public-access setting."*

## Decision

Put an **API Gateway HTTP API** (`aws_apigatewayv2_*`) in front of the Lambda:

- `aws_apigatewayv2_api` (protocol `HTTP`)
- `aws_apigatewayv2_integration` (`AWS_PROXY`, `payload_format_version = "2.0"`,
  `integration_uri = <lambda invoke_arn>`)
- `aws_apigatewayv2_route` (`route_key = "POST /"`)
- `aws_apigatewayv2_stage` (`$default`, `auto_deploy = true`)
- `aws_lambda_permission` granting `apigateway.amazonaws.com` invoke on the function

The stage's `invoke_url` becomes the Discord Interactions Endpoint URL. The Function
URL and its public permission are removed. **No handler change is required**: API
Gateway HTTP API payload format 2.0 delivers the same event shape (`headers`, `body`,
`isBase64Encoded`) the handler already reads, matching what Function URLs sent.

## Consequences

**Positive**
- Works in this account — the function stays private; only API Gateway is public.
- Keeps the account-wide "block public Lambdas" guardrail **on**. Public exposure is
  scoped to one explicit front door instead of disabling an account-level control.
- Mirrors a proven, already-running setup in a sibling project.

**Negative / costs**
- API Gateway HTTP API is **not free forever** (design goal #2): 1M requests/month
  free for 12 months, then ~$1 per million requests. Negligible for a personal bot
  (well under a dollar/year), but non-zero.
- One more resource type in the stack than a bare Function URL.

## Alternatives considered

| Option | Works here? | Notes |
|---|---|---|
| **API Gateway HTTP API** | **Yes** | Function stays private; guardrail intact; ~$1/M requests after free tier |
| **Lambda Function URL** | **No** | Free forever and simplest, but 403s under this account's Block Public Access |
| **Disable Lambda Block Public Access** | Would work | Restores free Function URLs, but **weakens security for the entire account** and needs a newer AWS CLI to toggle — rejected as the default posture |

## Open question (framework default)

It is not yet established whether Lambda Block Public Access is **on by default for new
AWS accounts** or was enabled on this one. If it is a common default, the framework's
blessed path should be API Gateway for everyone; if it is account-specific, Function
URLs (free, simpler) could remain the default with API Gateway documented as the
fallback. This should be verified before finalizing the setup docs' recommendation.
Supersedes the Function-URL choice implied by earlier infra; revisit if the default
turns out to be account-specific.
