terraform {
  required_version = ">= 1.6"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}

variable "cloudflare_zone_id" {
  type = string
}

variable "domain" {
  type    = string
  default = "firip.app"
}

variable "vercel_cname_target" {
  description = "Vercel-issued CNAME target for the apex/web app (from the Vercel domain settings page)."
  type        = string
  default     = "cname.vercel-dns.com"
}

variable "api_cname_target" {
  description = "Railway- or Fly-issued CNAME target for apps/api (from that platform's custom domain settings)."
  type        = string
  default     = ""
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

resource "cloudflare_record" "web" {
  zone_id = var.cloudflare_zone_id
  name    = "@"
  type    = "CNAME"
  content = var.vercel_cname_target
  proxied = false
}

resource "cloudflare_record" "api" {
  count   = var.api_cname_target == "" ? 0 : 1
  zone_id = var.cloudflare_zone_id
  name    = "api"
  type    = "CNAME"
  content = var.api_cname_target
  proxied = false
}
