terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region = "eu-west-2"
}

# s3 storage for backups
module "s3-private-bucket" {
  source                   = "registry.terraform.io/trussworks/s3-private-bucket/aws"
  version                  = "4.0.0"
  bucket                   = "{{ bucket_name }}"
  use_account_alias_prefix = false
}

module "s3_user" {
  source = "registry.terraform.io/cloudposse/iam-s3-user/aws"

  version      = "0.15.9"
  namespace    = "{{ bucket_name }}"
  stage        = "production"
  name         = "backupuser"
  s3_actions   = ["s3:*", "kms:Decrypt", "kms:GenerateDataKey"]
  s3_resources = [module.s3-private-bucket.arn, "${module.s3-private-bucket.arn}/*"]
}