variable "root_domain_name" {
  type        = string
  description = "Root domain name for the application"
  default     = "incidents.caves.org"
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
