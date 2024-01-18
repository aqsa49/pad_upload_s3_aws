# AWS Lambda Functions for Textract Processing

## Overview

This repository contains AWS Lambda functions written in Python for processing Textract responses and handling S3 events. The functions are designed to extract text information from PDF documents processed by Amazon Textract and store the results in CSV files.

## Prerequisites

1. **AWS Account:** Ensure that you have an active AWS account with the necessary permissions to create and manage Lambda functions, S3 buckets, and Textract jobs.

2. **AWS CLI Configuration:** Configure your AWS CLI with the necessary credentials to deploy and manage AWS resources.

3. **Environment Variables:** Set up the required environment variables for each Lambda function. Refer to the specific section in the code for the environment variables needed.

## Lambda Functions

### 1. `lambda_handler_textract_text_detection`

This Lambda function is triggered by S3 events when a PDF document is uploaded. It initiates a Textract text detection job and processes the results to create a CSV file with page-wise text information.

#### Environment Variables:

- `OUTPUT_BUCKET_NAME`: The name of the S3 bucket to store Textract job results.
- `OUTPUT_S3_PREFIX`: The S3 prefix for storing Textract job results.
- `SNS_TOPIC_ARN`: The ARN of the SNS topic to receive Textract job completion notifications.
- `SNS_ROLE_ARN`: The ARN of the IAM role assumed by SNS for publishing messages.

### 2. `lambda_handler_textract_process_response`

This Lambda function is triggered by SNS notifications when a Textract job is completed. It processes the Textract response, extracts page lines, and annotations, then creates a CSV file with the extracted information.

#### Environment Variables:

- `BUCKET_NAME`: The name of the S3 bucket where Textract job results are stored.
- `PREFIX`: The S3 prefix for Textract job results.

## Usage

1. Deploy the Lambda functions using the AWS Management Console, AWS CLI, or any other preferred deployment method.

2. Set up the required environment variables for each Lambda function in the AWS Lambda console.

3. Upload PDF documents to the specified S3 bucket, triggering the Textract text detection job.

4. Monitor the SNS notifications for job completion and observe the generated CSV files in the specified S3 bucket.

## Contributing

Contributions are welcome! Follow the [Contribution Guidelines](CONTRIBUTING.md) to contribute to this project.

## License

This project is licensed under the [MIT License](LICENSE).
