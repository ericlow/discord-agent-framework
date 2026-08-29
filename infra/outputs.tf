output "interactions_endpoint_url" {
  description = "Set this as the Interactions Endpoint URL in the Discord Developer Portal."
  value       = aws_apigatewayv2_stage.this.invoke_url
}

output "function_name" {
  description = "Lambda function name (use as LAMBDA_FUNCTION_NAME in CI)."
  value       = aws_lambda_function.this.function_name
}
