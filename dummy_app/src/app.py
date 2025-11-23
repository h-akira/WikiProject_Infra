import json
import os


def lambda_handler(event, context):
  """
  Dummy Lambda function that returns Hello World HTML
  """

  environment = os.environ.get('ENVIRONMENT', 'unknown')
  path = event.get('path', '/')
  method = event.get('httpMethod', 'GET')

  html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Wiki Project - Dummy App</title>
</head>
<body>
  <h1>Hello World!</h1>
  <p>Welcome to Wiki Project Dummy Application</p>
  <p>This is a placeholder application for development and testing purposes.</p>
  <hr>
  <p>Environment: {environment}</p>
  <p>Path: {path}</p>
  <p>Method: {method}</p>
  <hr>
  <p>Replace this stack with your actual application when ready.</p>
</body>
</html>"""

  return {
    'statusCode': 200,
    'headers': {
      'Content-Type': 'text/html',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    },
    'body': html_content
  }
