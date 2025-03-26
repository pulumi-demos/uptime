import pulumi
import pulumi_aws as aws

# Get AWS region from Pulumi configuration and create an explicit provider.
config = pulumi.Config()
default_region = config.require("region")
aws_provider = aws.Provider("aws-provider",
    region=default_region,
    default_tags=aws.ProviderDefaultTagsArgs(
        tags={
            "Environment": pulumi.get_stack(),
            "Project": pulumi.get_project(),
        }
    )
)

# Create an S3 bucket for storing Lambda code.
bucket = aws.s3.Bucket("uptime-code-bucket",
    acl="private",
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# Lambda execution role.
lambda_role = aws.iam.Role("uptime-role",
    assume_role_policy='''{
      "Version": "2012-10-17",
      "Statement": [{
        "Action": "sts:AssumeRole",
        "Principal": { "Service": "lambda.amazonaws.com" },
        "Effect": "Allow",
        "Sid": ""
      }]
    }''',
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# Attach basic Lambda execution policy.
aws.iam.RolePolicyAttachment("uptime-role-policy",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# Allow Lambda to access the S3 bucket.
aws.iam.RolePolicy("uptime-bucket-policy",
    role=lambda_role.id,
    policy=pulumi.Output.all(bucket.arn).apply(lambda args: f'''{{
      "Version": "2012-10-17",
      "Statement": [{{
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:ListBucket"],
        "Resource": ["{args[0]}", "{args[0]}/*"]
      }}]
    }}'''),
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# Lambda function definition.
function = aws.lambda_.Function("uptime-function",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("app")
    }),
    role=lambda_role.arn,
    handler="index.handler",
    runtime="python3.8",
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={"BUCKET_NAME": bucket.id}
    ),
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# Lambda function URL.
function_url = aws.lambda_.FunctionUrl("uptime-function-url",
    function_name=function.name,
    authorization_type="NONE",
    cors=aws.lambda_.FunctionUrlCorsArgs(
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"]
    ),
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# CloudWatch alarm for Lambda errors.
error_alarm = aws.cloudwatch.MetricAlarm("uptime-error-alarm",
    name="uptime-function-errors",
    comparison_operator="GreaterThanThreshold",
    evaluation_periods=2,
    metric_name="Errors",
    namespace="AWS/Lambda",
    period=10,
    statistic="Sum",
    threshold=1,
    dimensions={"FunctionName": function.name},
    alarm_description="Alarm when Lambda function has errors",
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# Create a Route53 health check for the Lambda function URL.
health_check = aws.route53.HealthCheck("uptime-health-check",
    type="HTTPS",
    fqdn=function_url.function_url.apply(lambda url: url.replace("https://", "").split("/")[0]),
    resource_path="/",  # adjust if your endpoint requires a different path
    port=443,
    request_interval=10,
    failure_threshold=2,
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# CloudWatch dashboard with Lambda metrics and Route53 health check status.
dashboard = aws.cloudwatch.Dashboard("uptime-monitoring-dashboard",
    dashboard_name="uptime-monitoring-dashboard",
    dashboard_body=pulumi.Output.all(function.name, health_check.id).apply(lambda args: f'''{{
      "widgets": [
        {{
          "type": "metric",
          "properties": {{
            "metrics": [
              ["AWS/Lambda", "Invocations", "FunctionName", "{args[0]}"]
            ],
            "period": 60,
            "stat": "Sum",
            "region": "{default_region}",
            "title": "Lambda Invocations"
          }}
        }},
        {{
          "type": "metric",
          "properties": {{
            "metrics": [
              ["AWS/Lambda", "Duration", "FunctionName", "{args[0]}"]
            ],
            "period": 60,
            "stat": "Average",
            "region": "{default_region}",
            "title": "Lambda Duration"
          }}
        }},
        {{
          "type": "metric",
          "properties": {{
            "metrics": [
              ["AWS/Lambda", "Errors", "FunctionName", "{args[0]}"]
            ],
            "period": 60,
            "stat": "Sum",
            "region": "{default_region}",
            "title": "Lambda Errors"
          }}
        }},
        {{
          "type": "metric",
          "properties": {{
            "metrics": [
              ["AWS/Lambda", "Throttles", "FunctionName", "{args[0]}"]
            ],
            "period": 60,
            "stat": "Sum",
            "region": "{default_region}",
            "title": "Lambda Throttles"
          }}
        }},
        {{
          "type": "metric",
          "properties": {{
            "metrics": [
              ["AWS/Route53", "HealthCheckStatus", "HealthCheckId", "{args[1]}"]
            ],
            "period": 60,
            "stat": "Average",
            "region": "{default_region}",
            "title": "Route53 Health Check Status"
          }}
        }}
      ]
    }}'''),
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# Export relevant outputs.
pulumi.export("uptime_function_url", function_url.function_url)
pulumi.export("uptime_dashboard_url", pulumi.Output.concat(
    "https://console.aws.amazon.com/cloudwatch/home?region=", default_region,
    "#dashboards:name=", dashboard.dashboard_name
))
