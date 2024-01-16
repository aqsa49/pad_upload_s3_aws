"""
-*- coding: utf-8 -*-
========================
========================
"""

import os
import json
import boto3
import pandas as pd


def lambda_handler(event, context):

    BUCKET_NAME = os.environ["BUCKET_NAME"]
    PREFIX = os.environ["PREFIX"]

    job_id = json.loads(event["Records"][0]["Sns"]["Message"])["JobId"]

    document_data = process_response(job_id)

    # Convert the document_data dictionary to a DataFrame
    df = pd.DataFrame(document_data)

    csv_key_name = f"{job_id}.csv"
    df.to_csv(f"/tmp/{csv_key_name}", index=False)

    upload_to_s3(f"/tmp/{csv_key_name}", BUCKET_NAME, f"{PREFIX}/{csv_key_name}")
    print(df)

    return {"statusCode": 200, "body": json.dumps("File uploaded successfully!")}


def upload_to_s3(filename, bucket, key):
    s3 = boto3.client("s3")
    s3.upload_file(Filename=filename, Bucket=bucket, Key=key)


def process_response(job_id):
    textract = boto3.client("textract")

    response = []
    pages = []

    response = textract.get_document_text_detection(JobId=job_id)
    pages.append(response)

    next_token = response.get("NextToken")
    while next_token:
        response = textract.get_document_text_detection(JobId=job_id, NextToken=next_token)
        pages.append(response)
        next_token = response.get("NextToken")

    document_data = {"PageNo": [], "BlockType": [], "Text": []}

    for page in pages:
        for item in page["Blocks"]:
            block_type = item["BlockType"]
            text = item.get("Text", "")

            document_data["PageNo"].append(item["Page"])
            document_data["BlockType"].append(block_type)
            document_data["Text"].append(text)

    return document_data

