# CloudVault

A desktop document manager built with Python and AWS services (S3, DynamoDB, SQS, SNS), tested locally using the Floci AWS emulator.

## Features
- Upload files with custom tags
- Search files by name or tag
- Download and delete files
- Activity log for every upload, download and delete (SQS)
- Event notifications via SNS
- Simple desktop GUI built with Tkinter

## Architecture
| Service | Purpose |
|---|---|
| S3 | Stores the uploaded files |
| DynamoDB | Stores file metadata (name, tag, size, timestamp) |
| SQS | Logs every action as an event |
| SNS | Publishes notifications for each action |

## Tech Stack
Python, boto3, Tkinter, AWS (S3, DynamoDB, SQS, SNS), Docker, Floci

## Setup
1. Install Docker Desktop and Python 3
2. Install the Floci CLI and start it: `floci start`
3. Install dependencies: `python -m pip install boto3`
4. Run the app: `python app.py`

The app connects to `http://localhost:4566` using dummy credentials.

## Note
This project runs against the Floci local AWS emulator. To use real AWS, remove `endpoint_url` and the dummy credentials in `app.py` and configure your own AWS credentials.

## Screenshots
.png/.jpg
