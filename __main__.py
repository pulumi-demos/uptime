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

# A shared S3 bucket
bucket = aws.s3.Bucket("shared-bucket",
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
error_rate_alarm = aws.cloudwatch.MetricAlarm("uptime-error-rate-alarm",
    name="uptime-function-error-rate",
    comparison_operator="GreaterThanThreshold",
    evaluation_periods=2,
    threshold=0.1,  # error rate threshold in percentage
    metric_queries=[
        {
            "id": "m1",
            "metric": {
                "namespace": "AWS/Lambda",
                "metricName": "Invocations",
                "dimensions": {"FunctionName": function.name},
                "period": 60,
                "stat": "Sum",
            },
            "return_data": False,
        },
        {
            "id": "m2",
            "metric": {
                "namespace": "AWS/Lambda",
                "metricName": "Errors",
                "dimensions": {"FunctionName": function.name},
                "period": 60,
                "stat": "Sum",
            },
            "return_data": False,
        },
        {
            "id": "e1",
            "expression": "m2/m1*100",
            "label": "Error Rate (%)",
            "return_data": True,
        }
    ],
    alarm_description="Alarm when Lambda error rate exceeds threshold",
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

# CloudWatch dashboard with SRE metrics (percentages).
dashboard = aws.cloudwatch.Dashboard("uptime-service-dashboard",
    dashboard_name="uptime-service-dashboard",
    dashboard_body=pulumi.Output.all(function.name).apply(
        lambda args: f'''{{
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
        "title": "Traffic: Total Requests"
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
        "title": "Latency: Average Duration (ms)"
      }}
    }},
    {{
      "type": "metric",
      "properties": {{
        "metrics": [
          ["AWS/Lambda", "Invocations", "FunctionName", "{args[0]}", {{"id": "m1", "visible": false}}],
          ["AWS/Lambda", "Errors", "FunctionName", "{args[0]}", {{"id": "m2", "visible": false}}],
          [{{"expression": "m2/m1*100", "label": "Error Rate (%)", "id": "e1"}}]
        ],
        "period": 60,
        "region": "{default_region}",
        "title": "Errors: Error Rate (%)"
      }}
    }},
    {{
      "type": "metric",
      "properties": {{
        "metrics": [
          ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", "{args[0]}"]
        ],
        "period": 60,
        "stat": "Maximum",
        "region": "{default_region}",
        "title": "Saturation: Concurrent Executions"
      }}
    }}
  ]
}}'''
    ),
    opts=pulumi.ResourceOptions(provider=aws_provider)
)

# Export relevant outputs.
pulumi.export("uptime_function_url", function_url.function_url)
pulumi.export("uptime_dashboard_url", pulumi.Output.concat(
    "https://console.aws.amazon.com/cloudwatch/home?region=", default_region,
    "#dashboards:name=", dashboard.dashboard_name
))
