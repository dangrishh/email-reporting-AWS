import boto3, logging, urllib.parse, re, json, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+ only

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client('s3')
sesv2 = boto3.client('sesv2')  # Make sure SESv2 is supported in your region

# Load environment variables
email_sender = os.getenv("EMAIL_SENDER")
email_recipient = os.getenv("EMAIL_RECIPIENT").replace(" ", "").split(",")
debug_mode = os.getenv("DEBUG_MODE")

logger.info(f"EMAIL_SENDER: {email_sender}, EMAIL_RECIPIENT: {email_recipient}, DEBUG_MODE: {debug_mode}")

def lambda_handler(event, context):
    try:
        logger.info("Lambda triggered with event: %s", json.dumps(event))

        # Extract S3 bucket and object key from event
        records = event['Records'][0]['s3']
        bucket = records['bucket']['name']
        directory = urllib.parse.unquote_plus(records['object']['key'], encoding='utf-8')
        logger.info(f"S3 bucket: {bucket}, Key: {directory}")

        # Retrieve file content from S3
        response = s3.get_object(Bucket=bucket, Key=directory)
        file_content = response['Body'].read()
        logger.info("File content retrieved from S3.")

        # Extract filename and derive report name
        filename = directory.split('/')[-1]
        logger.info(f"Filename extracted: {filename}")

        # Extract date from filename (e.g. 2025-07-14T14:00:00Z)
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}:\d{2}Z", filename)
        if not date_match:
            raise ValueError("No valid timestamp found in filename.")

        report_date_obj = datetime.strptime(date_match.group(1), "%Y-%m-%d")
        report_date = report_date_obj.strftime('%B %d, %Y')
        logger.info(f"Report date derived from filename: {report_date}")

        # Remove timestamp suffix from filename to get report title
        report_name = re.sub(r"-\d{4}-\d{2}-\d{2}T\d{2}[:_]\d{2}[:_]\d{2}Z\.csv$", "", filename)
        report_recipient = report_name.split(' - ')[0]
        logger.info(f"Report name extracted: {report_name}")

        # Construct email subject and body
        email_subject = f"[EXT] {report_name}"
        logger.info(f"Email subject: {email_subject}")

        # Email body text
        email_body = (
            "External email: Please exercise caution.\n\n"
            f"Hi {report_recipient} Team,\n\n"
            f"Please see attached {report_name} for {report_date} from Amazon Connect."
        )

        # Compose email with attachment
        mime_email = MIMEMultipart()
        mime_email['Subject'] = email_subject  
        mime_email['From'] = email_sender
        mime_email['To'] = ", ".join(email_recipient)

        # Attach text content
        mime_email.attach(MIMEText(email_body))
        logger.info("Email body constructed.")

        # Attach the CSV file
        attachment = MIMEApplication(file_content)
        attachment.add_header('Content-Disposition', 'attachment', filename=filename)
        mime_email.attach(attachment)
        logger.info(f"Attachment added: {filename}")

        # Send email using Amazon SES v2
        sesv2.send_email(
            FromEmailAddress=email_sender,
            Destination={'ToAddresses': email_recipient},
            Content={'Raw': {'Data': mime_email.as_bytes()}}
        )
        logger.info("Email sent successfully via SESv2.")

        return {
            "status": 200,
            "message": "Email sent successfully.",
            "file": filename
        }

    except Exception as e:
        logger.exception("An error occurred during email processing.")
        return {
            "status": 500,
            "message": str(e)
        }
