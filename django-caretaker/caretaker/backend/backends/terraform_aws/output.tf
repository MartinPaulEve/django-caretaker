output "access_key" {
  description = "The access key of the S3 backup user"
  value       = module.s3_user.access_key_id
  sensitive   = true
}

output "backup_secret_key" {
  description = "The secret key of the S3 backup user"
  value       = module.s3_user.secret_access_key
  sensitive   = true
}
