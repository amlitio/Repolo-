# Terraform (infrastructure-as-code scaffold)

This directory is a minimal scaffold, not a deployable Terraform root
module. FIRIP's primary deployment path (Railway for `apps/api` /
`apps/workers`, Vercel for `apps/web`) is managed through each platform's
own dashboard/config-as-code (see `../railway/`, `../vercel/`), since
neither Railway nor Vercel's Terraform providers are necessary for an MVP
of this size.

What's here covers the one piece of infrastructure that benefits from
being declarative even at MVP scale: DNS, if/when FIRIP moves off
platform-issued subdomains onto a custom domain.

- `dns.tf` — a Cloudflare provider stub for the apex domain and the `api.`
  subdomain CNAME, commented out pending a real domain/account.

To use this:

```bash
cd infra/terraform
terraform init
# fill in terraform.tfvars (not committed - see .gitignore) with your
# Cloudflare API token and zone ID
terraform plan
```

This was never run against a real Cloudflare account in the sandbox this
repo was built in — treat it as a starting point, not a verified module.
