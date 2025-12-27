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

variable "origin_domain_name" {
  type        = string
  description = "Domain name for the origin web server for the frontend"
  default     = "origin.incidents.caves.org"
}

variable "api_domain_name" {
  type        = string
  description = "Domain name for the API"
  default     = "api.incidents.caves.org"
}
