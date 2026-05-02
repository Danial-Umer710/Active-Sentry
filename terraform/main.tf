provider "aws" {
  region = "eu-north-1"
}

# 1. GENERATE THE PRIVATE KEY (The "Master Key")
resource "tls_private_key" "sentry_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# 2. SAVE THE KEY TO YOUR LAPTOP (So you can SSH)
resource "local_file" "sentry_key_file" {
  content         = tls_private_key.sentry_key.private_key_pem
  filename        = "sentry-key.pem"
  file_permission = "0400"
}

# 3. UPLOAD THE PUBLIC KEY TO AWS (The "Lock")
resource "aws_key_pair" "sentry_key_pair" {
  key_name   = "sentry-key"
  public_key = tls_private_key.sentry_key.public_key_openssh
}

# 4. THE SECURITY GROUP (The Firewall)
resource "aws_security_group" "active_sentry_sg" {
  name        = "active-sentry-security-group"
  description = "Allow SSH, K3s, and Active-Sentry traffic"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 30080
    to_port     = 30080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 5. THE SERVER (The Hardware)
resource "aws_instance" "active_sentry_server" {
  ami                    = "ami-09a9858973b288bdd" # Ubuntu 24.04 Stockholm
  instance_type          = "t3.micro"
  key_name               = aws_key_pair.sentry_key_pair.key_name
  vpc_security_group_ids = [aws_security_group.active_sentry_sg.id]

  tags = {
    Name = "Active-Sentry-Server"
  }
}

# 6. THE OUTPUT
output "public_ip" {
  value = aws_instance.active_sentry_server.public_ip
}
