locals {
  cdn_origin_id      = "S3-${module.cdn_bucket.s3_bucket_id}"
  api_origin_id      = "API-${var.frontend_domain_name}"
  frontend_origin_id = "HTTP-NSSIncidentDB"
}

resource "aws_cloudfront_origin_access_identity" "cdn" {
  comment = "NSS Incident DB CDN"
}

resource "aws_cloudfront_cache_policy" "default_with_query_strings" {
  name        = "CachingOptimizedWithQueryStrings"
  comment     = "Caching optimized with query strings in cache key"
  default_ttl = 86400
  max_ttl     = 31536000
  min_ttl     = 1

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }

    headers_config {
      header_behavior = "none"
    }

    query_strings_config {
      query_string_behavior = "all"
    }

    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
  }
}

resource "aws_cloudfront_cache_policy" "api_cache" {
  name        = "APICachePolicy"
  comment     = "Cache API GET requests with query strings"
  default_ttl = 0
  max_ttl     = 86400
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }

    headers_config {
      header_behavior = "none"
    }

    query_strings_config {
      query_string_behavior = "all"
    }
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
  }
}

resource "aws_cloudfront_origin_request_policy" "api_origin" {
  name    = "APIOriginRequestPolicy"
  comment = "Forward necessary headers and cookies to API origin"

  cookies_config {
    cookie_behavior = "all"
  }

  headers_config {
    header_behavior = "whitelist"
    headers {
      items = ["Origin", "Accept", "Content-Type"]
    }
  }

  query_strings_config {
    query_string_behavior = "all"
  }
}

resource "aws_cloudfront_function" "strip_cdn_prefix" {
  name    = "strip-cdn-prefix"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = <<-EOF
    function handler(event) {
      var request = event.request;
      request.uri = request.uri.replace(/^\/cdn/, '');
      return request;
    }
  EOF
}

resource "aws_cloudfront_function" "strip_admin_prefix" {
  name    = "strip-admin-prefix"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = <<-EOF
    function handler(event) {
      var request = event.request;
      request.uri = request.uri.replace(/^\/admin/, '');
      return request;
    }
  EOF
}

resource "aws_cloudfront_distribution" "cdn" {
  aliases             = [var.frontend_domain_name]
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CIDB CDN"
  default_root_object = "index.html"
  price_class         = "PriceClass_All"

  origin {
    domain_name = module.cdn_bucket.s3_bucket_bucket_regional_domain_name
    origin_id   = local.cdn_origin_id

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.cdn.cloudfront_access_identity_path
    }
  }

  origin {
    domain_name = var.api_domain_name
    origin_id   = local.api_origin_id

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  origin {
    domain_name = var.origin_domain_name
    origin_id   = local.frontend_origin_id

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  ordered_cache_behavior {
    path_pattern           = "/api/v1/*"
    target_origin_id       = local.api_origin_id
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Origin", "Accept", "Content-Type"]
      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  ordered_cache_behavior {
    path_pattern           = "/admin/*"
    target_origin_id       = local.api_origin_id
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.strip_admin_prefix.arn
    }

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Origin", "Accept", "Content-Type"]
      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  ordered_cache_behavior {
    path_pattern           = "/cdn/*"
    target_origin_id       = local.cdn_origin_id
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.strip_cdn_prefix.arn
    }

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0

    default_ttl = 60
    max_ttl     = 3600
    compress    = true

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    target_origin_id = local.frontend_origin_id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn = module.wildcard_cert.acm_certificate_arn
    ssl_support_method  = "sni-only"
  }

  provider = aws.use1
}
