locals {
  cdn_origin_id      = "S3-${module.cdn_bucket.s3_bucket_id}"
  api_origin_id      = "API-${var.frontend_domain_name}"
  frontend_origin_id = "S3-${module.frontend_bucket.s3_bucket_id}"
}

resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "cidb-s3-oac"
  description                       = "OAC for CIDB S3 origins"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
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
      items = ["Origin", "Accept", "Content-Type", "X-CSRFToken", "Referer"]
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

resource "aws_cloudfront_function" "spa_rewrite" {
  name    = "spa-rewrite"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = <<-EOF
    function handler(event) {
      var request = event.request;
      var last = request.uri.split('/').pop();
      if (last.indexOf('.') === -1) {
        request.uri = '/index.html';
      }
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
  price_class         = "PriceClass_100"

  origin {
    domain_name              = module.frontend_bucket.s3_bucket_bucket_regional_domain_name
    origin_id                = local.frontend_origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
  }

  origin {
    domain_name              = module.cdn_bucket.s3_bucket_bucket_regional_domain_name
    origin_id                = local.cdn_origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
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

  ordered_cache_behavior {
    path_pattern             = "/api/v1/*"
    target_origin_id         = local.api_origin_id
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    viewer_protocol_policy   = "redirect-to-https"
    compress                 = true
    cache_policy_id          = aws_cloudfront_cache_policy.api_cache.id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.api_origin.id
  }

  ordered_cache_behavior {
    path_pattern             = "/admin/*"
    target_origin_id         = local.api_origin_id
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    viewer_protocol_policy   = "redirect-to-https"
    compress                 = true
    cache_policy_id          = aws_cloudfront_cache_policy.api_cache.id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.api_origin.id
  }

  ordered_cache_behavior {
    path_pattern             = "/static/*"
    target_origin_id         = local.api_origin_id
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    viewer_protocol_policy   = "redirect-to-https"
    compress                 = true
    cache_policy_id          = aws_cloudfront_cache_policy.api_cache.id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.api_origin.id
  }

  ordered_cache_behavior {
    path_pattern           = "/cdn/*"
    target_origin_id       = local.cdn_origin_id
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
    cache_policy_id        = data.aws_cloudfront_cache_policy.caching_optimized.id

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.strip_cdn_prefix.arn
    }
  }

  default_cache_behavior {
    target_origin_id       = local.frontend_origin_id
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
    cache_policy_id        = data.aws_cloudfront_cache_policy.caching_optimized.id

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa_rewrite.arn
    }
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
