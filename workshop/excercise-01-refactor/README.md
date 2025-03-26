# Workshop Exercise: Refactoring the Monolith Application

In this exercise, you'll refactor the existing monolith application into separate, focused services. The goal is to create a modular architecture using Pulumi where shared resources are managed independently and referenced by other projects.

## Exercise Overview

1. **Phase 1: Split the Monolith**  
   Refactor the monolith into two separate Pulumi projects:
   - **Shared Services Project:**  
     Contains common resources (e.g., an S3 bucket) that will be used across multiple services.
   - **Uptime Service Project:**  
     Contains the Lambda uptime service which monitors application health and uses the shared S3 bucket via stack outputs.

2. **Phase 2: Introduce a New Service**  
   Create a third Pulumi project:
   - **New Service Project:**  
     A service that writes items (files) to the shared S3 bucket, demonstrating resource sharing across projects.

At the end of this exercise, you will have three Pulumi projects:

- **Shared Services:** Contains the S3 bucket and any other shared infrastructure.
- **Uptime Service:** The original Lambda uptime service using the shared bucket.
- **New Service:** A service that writes files to the shared S3 bucket.

## Detailed Steps

### Phase 1: Refactoring the Monolith

1. **Create the Shared Services Project:**
   - Extract common resources (e.g., the S3 bucket) from the monolith.
   - Export these resources (such as the bucket name or ARN) as stack outputs.

2. **Create the Uptime Service Project:**
   - Move the Lambda uptime service into its own project.
   - Modify the Lambda function to reference the shared S3 bucket using Pulumi stack references.  
     Use Pulumi’s stack reference to import the bucket name exported by the Shared Services stack.

3. **Verify Integration:**
   - Deploy both projects and ensure that the uptime service successfully uses the shared bucket.

### Phase 2: Adding a New Service

1. **Create the New Service Project:**
   - Develop a new Pulumi project that implements a service to write files to the shared S3 bucket.
   - Use Pulumi stack references to obtain the S3 bucket details from the Shared Services project.

2. **Deploy and Test:**
   - Deploy the New Service project.
   - Validate that the new service correctly writes files to the S3 bucket and that all projects interact seamlessly.

## How It Works

- **AWS Lambda Function:**  
  The Lambda function (defined in `lambda/index.py`) checks for the required `BUCKET_NAME` environment variable and attempts to access the specified S3 bucket. If the bucket is unreachable or encounters errors, the function fails; otherwise, it returns a `200` response with the bucket name and object count.

- **Function URL:**  
  The Lambda function is exposed via a Function URL, allowing public access for health checks.

- **Route53 Health Check:**  
  Configured to run every 10 seconds, it pings the Lambda Function URL and verifies a healthy `200` response.

- **CloudWatch Metrics and Dashboard:**  
  Metrics such as total invocations (Traffic: Total Requests), average latency (Latency: Average Duration), error rate (Errors: Error Rate (%)), and concurrent executions (Saturation: Concurrent Executions) are visualized on a CloudWatch dashboard designed around the SRE principles and the four golden signals.

- **CloudWatch Alarms:**  
  An alarm monitors the Lambda error rate using metric math. It calculates the error rate as `(Errors / Invocations) * 100` and triggers if it exceeds 0.1% for two consecutive evaluation periods, ensuring any service degradation is promptly flagged.

## Golden Signals: The Four Pillars of Monitoring

To maintain high service reliability, we monitor these four key metrics:

- **Latency:**  
  How long it takes to process a request.  
  *Quick responses indicate a healthy system.*

- **Traffic:**  
  The volume of incoming requests.  
  *Helps gauge the load on your system.*

- **Errors:**  
  The rate of failed requests.  
  *A spike can signal underlying issues.*

- **Saturation:**  
  The level of resource utilization (e.g., concurrent executions).  
  *High saturation may indicate nearing capacity limits.*

These signals provide a clear, real-time view of system performance and help trigger timely interventions.

## Deliverables

By the end of this workshop, you should have:

- **Three Pulumi Projects:**
  1. **Shared Services:** Managing shared resources like the S3 bucket.
  2. **Uptime Service:** A Lambda-based uptime monitoring service referencing the shared bucket.
  3. **Writer Service:** A service that writes files to the shared S3 bucket.
- **Documentation:**  
  A clear structure showing how stack outputs are shared and consumed between projects.
- **Working Integration:**  
  Each project correctly interacting with the shared resources.

## Next Steps

1. **Review Your Monolith:**  
   Identify and extract common resources into the Shared Services project.
2. **Create and Configure Projects:**  
   Set up separate Pulumi projects and configure stack outputs/references.
3. **Develop and Test:**  
   Deploy your projects and validate the interactions.
4. **Introduce the New Service:**  
   Build and integrate the file-writing service, ensuring it uses the shared S3 bucket.
5. **Share Learnings:**  
   Discuss any challenges or insights gained during the refactoring process.

Happy coding and refactoring!
