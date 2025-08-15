# email-reporting-AWS

Lambda Function: Automated Report Emailer via SESv2
This AWS Lambda function is triggered by an S3 event when a new report (CSV file) is uploaded. It performs the following tasks:

Parses the S3 event to get the uploaded file's bucket and key.

Retrieves the file content from S3.

Extracts metadata (filename, report date, recipient) from the file name.

Builds an email with a subject, body, and the file as an attachment.

Sends the email via Amazon SESv2 to the configured recipients.

Environment variables used:

EMAIL_SENDER: The verified SES sender email

EMAIL_RECIPIENT: Comma-separated recipient list

DEBUG_MODE: Optional flag for enabling debug
