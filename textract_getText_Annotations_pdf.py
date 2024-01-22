# -*- coding: utf-8 -*-
# ========================
#  Aqsa Murtaza
# ========================

# Import necessary libraries
import os
import json
import boto3
import pandas as pd
from PyPDF2 import PdfReader
from io import BytesIO

# Lambda function handler
def lambda_handler(event, context):
    # Retrieve environment variables
    BUCKET_NAME = os.environ["BUCKET_NAME"]
    PREFIX = os.environ["PREFIX"]

    # Extract information from SNS message
    job_info = json.loads(event["Records"][0]["Sns"]["Message"])
    job_id = job_info["JobId"]
    file_name = job_info['DocumentLocation']['S3ObjectName'].split('/')[-1]
    s3_bucket = job_info['DocumentLocation']['S3Bucket']
    s3_key = job_info['DocumentLocation']['S3ObjectName']

    # Process Textract response to get page lines and annotations
    page_lines, annotations = process_response(job_id)
    
    # Read the processed PDF file from S3 and process annotations
    annotations_list = process_pdf_annotations(s3_bucket, s3_key)

    # Convert annotations_list to a dictionary for easy retrieval
    pdf_annotations = {annotation['PageNo']: annotation['Annotation'] for annotation in annotations_list}
    
    # Combine both text and annotations into a single list
    combined_lines = [{'PageNo': page, 'Text': text, 'Annotation': pdf_annotations.get(page, "")} for page, text in page_lines.items()]


    # Generate CSV file name
    csv_key_name = file_name.replace(".pdf", ".csv")

    # Create a DataFrame from combined_lines and save it to a CSV file
    df = pd.DataFrame(combined_lines)
    df.to_csv(f"/tmp/{csv_key_name}", index=False)

    # Upload the CSV file to S3
    upload_to_s3(f"/tmp/{csv_key_name}", BUCKET_NAME, f"{PREFIX}/{csv_key_name}")


    # Print the collected annotations
    for annotation in annotations_list:
        print(f"Page {annotation['PageNo']}, Annotation: {annotation['Annotation']}")

    return {"statusCode": 200, "body": json.dumps("File uploaded and PDF annotations processed successfully!")}

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

# Function to upload a file to S3
def upload_to_s3(filename, bucket, key):
    s3 = boto3.client("s3")
    s3.upload_file(Filename=filename, Bucket=bucket, Key=key)

# Function to read processed PDF file from S3 and process annotations
def process_pdf_annotations(bucket, pdf_key):
    s3 = boto3.client("s3", region_name="us-east-1")  # Replace 'us-east-1' with your desired AWS region
    annotations_list = []  # List to store annotations

    try:
        # Get the object from S3
        s3obj = s3.get_object(Bucket=bucket, Key=pdf_key)

        # Read the PDF using PyPDF2
        pdf_content = s3obj["Body"].read()
        reader = PdfReader(BytesIO(pdf_content))

        for page_number, page in enumerate(reader.pages, start=1):
            try:
                if page.annotations is not None:
                    for annot in page.annotations:
                        for index, content in annot.items():
                            if isinstance(content, str) and "/Contents" in index:
                                annotations_list.append({"PageNo": page_number, "Annotation": content})
                                break
                else:
                    annotations_list.append({"PageNo": page_number, "Annotation": "No annotations."})
            except AttributeError:
                annotations_list.append({"PageNo": page_number, "Annotation": "Error processing annotations."})

    except Exception as e:
        annotations_list.append({"PageNo": 0, "Annotation": f"Error reading key {pdf_key} from bucket {bucket}: {e}"})

    return annotations_list
