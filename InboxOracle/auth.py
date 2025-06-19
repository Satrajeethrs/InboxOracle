#!/usr/bin/env python3

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from loguru import logger
import os.path
import pickle

# Gmail API scopes required for reading and modifying emails
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """
    Handles the Gmail API OAuth 2.0 flow and returns an authenticated service.
    Creates or loads credentials and returns the Gmail API service object.
    
    Returns:
        service: Authenticated Gmail API service object
    """
    creds = None
    
    # Load existing credentials from token.pickle if present
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing credentials: {e}")
                return None
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Error in OAuth flow: {e}")
                return None
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    try:
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail API service created successfully")
        return service
    except Exception as e:
        logger.error(f"Error building Gmail service: {e}")
        return None

if __name__ == '__main__':
    # Test the authentication
    service = get_gmail_service()
    if service:
        logger.success("Authentication successful!")
    else:
        logger.error("Authentication failed!")