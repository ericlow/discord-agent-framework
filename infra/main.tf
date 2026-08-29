terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Local state (ADR-004): no remote backend.
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

locals {
  # Constructed ahead of the function so the self-invoke policy doesn't create a
  # cycle (policy -> function -> role -> policy).
  function_arn = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.function_name}"
  package_path = "${path.module}/../function.zip"
}

# --- IAM ---

resource "aws_iam_role" "lambda_exec" {
  name = "${var.function_name}-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# CloudWatch Logs.
resource "aws_iam_role_policy_attachment" "basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Allow the function to invoke itself for engine mode.
resource "aws_iam_role_policy" "self_invoke" {
  name = "${var.function_name}-self-invoke"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = local.function_arn
    }]
  })
}

# --- Logs ---

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 14
}

# --- Lambda ---

resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = aws_iam_role.lambda_exec.arn
  runtime       = "python3.12"
  handler       = "examples.research_agent.handler.handler"

  filename         = local.package_path
  source_code_hash = filebase64sha256(local.package_path)

  timeout     = 300
  memory_size = 512

  environment {
    variables = {
      # AWS_LAMBDA_FUNCTION_NAME and AWS_REGION are provided by the runtime.
      DISCORD_PUBLIC_KEY     = var.discord_public_key
      DISCORD_APPLICATION_ID = var.discord_application_id
      DISCORD_BOT_TOKEN      = var.discord_bot_token
      ANTHROPIC_API_KEY      = var.anthropic_api_key
      JINA_API_KEY           = var.jina_api_key
      DATABASE_URL           = var.database_url
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.basic,
    aws_cloudwatch_log_group.lambda,
  ]
}

# --- Public ingress: API Gateway HTTP API (ADR-005) ---
#
# We front the Lambda with an API Gateway HTTP API instead of a Lambda Function
# URL: this account has Lambda Block Public Access enabled, so Function URLs 403
# regardless of their resource policy. API Gateway keeps the function private and
# is the public entrance. Payload format 2.0 matches the event shape the handler
# already expects (same as a Function URL).

resource "aws_apigatewayv2_api" "this" {
  name          = "${var.function_name}-interactions"
  protocol_type = "HTTP"
  description   = "Discord interactions endpoint for the ${var.function_name} agent"
}

resource "aws_apigatewayv2_integration" "this" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.this.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "this" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /"
  target    = "integrations/${aws_apigatewayv2_integration.this.id}"
}

resource "aws_apigatewayv2_stage" "this" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true
}

# Allow API Gateway to invoke the function.
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}
