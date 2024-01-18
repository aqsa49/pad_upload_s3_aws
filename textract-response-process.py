import os
import json
import boto3
import pandas as pd

# Lambda function handler
def lambda_handler(event, context):
    # Retrieve environment variables
    BUCKET_NAME = os.environ["BUCKET_NAME"]
    PREFIX = os.environ["PREFIX"]

    # Extract information from SNS message
    job_id = json.loads(event["Records"][0]["Sns"]["Message"])["JobId"]
    file_name = json.loads(event["Records"][0]["Sns"]["Message"])['DocumentLocation']['S3ObjectName'].split('/')[-1]

    # Process Textract response to get page lines and annotations
    page_lines, annotations = process_response(job_id)

    # Exclude the page number
    page_lines = {page: text for page, text in page_lines.items() if not text.isdigit()}

    # Add annotations to page_lines
    for page, annotation_text in annotations.items():
        if page in page_lines:
            page_lines[page] += f" {annotation_text}"
        else:
            page_lines[page] = annotation_text

    # Generate CSV file name
    csv_key_name = file_name.replace(".pdf",".csv")

    # Create a DataFrame from page_lines and save it to a CSV file
    df = pd.DataFrame(page_lines.items())
    df.columns = ["PageNo", "Text"]
    df.to_csv(f"/tmp/{csv_key_name}", index=False)

    # Upload the CSV file to S3
    upload_to_s3(f"/tmp/{csv_key_name}", BUCKET_NAME, f"{PREFIX}/{csv_key_name}")
    print(df)

    return {"statusCode": 200, "body": json.dumps("File uploaded successfully!")}

# Function to upload a file to S3
def upload_to_s3(filename, bucket, key):
    s3 = boto3.client("s3")
    s3.upload_file(Filename=filename, Bucket=bucket, Key=key)

# Function to process Textract response
def process_response(job_id):
    textract = boto3.client("textract")

    response = {}
    pages = []

    # Get the document text detection response
    response = textract.get_document_text_detection(JobId=job_id)

    pages.append(response)

    nextToken = None
    if "NextToken" in response:
        nextToken = response["NextToken"]

    # Retrieve additional pages if available
    while nextToken:
        response = textract.get_document_text_detection(
            JobId=job_id, NextToken=nextToken
        )
        pages.append(response)
        nextToken = None
        if "NextToken" in response:
            nextToken = response["NextToken"]

    # Extract lines and annotations from Textract response
    page_lines = {}
    annotations = {}

    for page in pages:
        for item in page["Blocks"]:
            if item["BlockType"] == "LINE":
                if item["Page"] in page_lines:
                    page_lines[item["Page"]] += f" {item['Text']}"  # Concatenate the text
                else:
                    page_lines[item["Page"]] = item["Text"]
            elif item["BlockType"] == "ANNOTATION":
                if item["Page"] in annotations:
                    annotations[item["Page"]] += f" {item['Text']}"  # Concatenate annotation text
                else:
                    annotations[item["Page"]] = item["Text"]

    return page_lines, annotations
