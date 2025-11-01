terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# BUG: variable non definita o tag duplicati da fixare
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project}-logs"
  tags = {
    Project = var.project
    Project = var.project # <- errore
  }
}
