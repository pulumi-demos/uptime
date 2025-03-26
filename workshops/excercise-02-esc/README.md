# Exercise 02: Integrate ESC with pulumi-stacks Provider

## Overview

In this exercise, you will update your project to leverage the **pulumi-stacks** provider to import stack outputs (ESC) from other Pulumi stacks. This decouples environment-specific configuration from your code by dynamically retrieving the latest outputs from shared infrastructure defined in the Pulumi Cloud Portal.

Unlike previous examples that were VPC-specific, this exercise uses a generic example. You'll create an ESC definition in the Pulumi Cloud Portal with outputs relevant to your code base and then reference that environment in your Pulumi stack configuration.

## Objectives

- **Create the ESC Definition:**  
  In the Pulumi Cloud Portal, define an environment with the outputs your project requires.

- **Configure Your Stack:**  
  Update your Pulumi stack configuration (e.g., `Pulumi.<stack-name>.yaml`) to reference the environment definition. For example:

  ```yaml
    environment:
    - project/environment
  ```

- **Refactor Your Code:**  
  Modify your code to consume these dynamic configuration values using Pulumi's configuration API.

- **Validate Integration:**  
  Deploy the changes and confirm that your project successfully retrieves the configuration values via ESC.

## Instructions

1. **Create the ESC Definition in the Pulumi Cloud Portal**

   - Log in to the Pulumi Cloud Portal.
   - Create a new ESC definition for your project’s environment.
   - Define the necessary outputs, such as `sharedOutput` and `resourceArn`, that your code will need.

2. **Update Your Stack Configuration**

   Edit your `Pulumi.<stack-name>.yaml` file to reference the environment definition. Replace `<stack-name>` with your actual stack name. Your configuration should include an `environment` block and a values section like this:

   ```yaml
   values:
     stackRefs:
       fn::open::pulumi-stacks:
         stacks:
           sharedInfra:
             stack: shared-infra/dev
     pulumiConfig:
       sharedOutput: ${stackRefs.sharedInfra.sharedOutput}
       resourceArn: ${stackRefs.sharedInfra.resourceArn}
   ```

   This configuration instructs Pulumi to import outputs from the `shared-infra/dev` stack via the pulumi-stacks provider.

3. **Modify Your Code to Use Dynamic Config Values**

   In your project code (e.g., in `__main__.py`), update the configuration retrieval to use the new keys defined in your ESC. For example:

   ```python
   import pulumi

   config = pulumi.Config()
   shared_output = config.require("sharedOutput")
   resource_arn = config.require("resourceArn")
   # Use these values in your resource definitions as needed.
   ```

4. **Deploy and Validate**

   - Run `pulumi up` to deploy your changes.
   - Verify that your resources are correctly using the configuration values imported from the shared environment.
   - Confirm that any updates made in the Pulumi Cloud Portal ESC definition are automatically reflected in your stack without further code changes.

## Benefits

- **Centralized Configuration:**  
  Shared outputs are managed in one location (the Pulumi Cloud Portal), reducing redundancy and simplifying configuration management.

- **Dynamic Updates:**  
  Changes in the shared environment outputs are automatically propagated to your stacks, enhancing maintainability and reducing deployment friction.

- **Improved Modularity:**  
  Decoupling configuration from code results in a more modular architecture, making it easier to manage multiple projects that share common resources.

## Deliverables

By the end of this exercise, you should have:

- An ESC definition created in the Pulumi Cloud Portal with outputs relevant to your project.
- An updated `Pulumi.<stack-name>.yaml` file that references the environment.
- Code modifications that consume these dynamic configuration values.
- A successful deployment where shared outputs are correctly integrated into your project.

Happy coding and enjoy the benefits of dynamic, environment-agnostic configuration!
