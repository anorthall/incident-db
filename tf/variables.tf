variable "cloudflare_zone_id" {
  type        = string
  description = "ID of the existing Cloudflare zone for caves.org"
  default     = "6fb59bbb337572f22c08d626ad901165" # pragma: allowlist secret
}

variable "frontend_domain_name" {
  type        = string
  description = "Domain name for the frontend"
  default     = "incidents.caves.org"
}

variable "api_domain_name" {
  type        = string
  description = "Domain name for the API"
  default     = "api.incidents.caves.org"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type for the application server"
  default     = "t4g.small"
}
