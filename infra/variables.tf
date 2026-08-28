variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "function_name" {
  description = "Name of the Lambda function."
  type        = string
  default     = "discord-agent"
}

variable "discord_public_key" {
  description = "Discord application public key (for Ed25519 verification)."
  type        = string
}

variable "discord_application_id" {
  description = "Discord application ID."
  type        = string
}

variable "discord_bot_token" {
  description = "Discord bot token."
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API key."
  type        = string
  sensitive   = true
}

variable "jina_api_key" {
  description = "Jina API key (for the built-in web tools)."
  type        = string
  sensitive   = true
}

variable "database_url" {
  description = "Postgres connection string (Neon pooled endpoint)."
  type        = string
  sensitive   = true
}
