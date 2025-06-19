#!/usr/bin/env python3

from auth import get_gmail_service
from models import Email, init_db
from loguru import logger
import base64
from email.utils import parsedate_to_datetime

def parse_email_date(date_str):
    """Convert email date string to datetime object"""
    try:
        return parsedate_to_datetime(date_str)
    except Exception as e:
        logger.error(f"Error parsing date: {e}")
        from datetime import datetime
        return datetime.now()

def get_email_body(message):
    """Extract email body from message payload"""
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode()
    return message.get_payload(decode=True).decode() if message.get_payload() else ""

def fetch_and_store_emails(max_results=None):
    """
    Fetch emails from Gmail API and store them in SQLite database.
    
    Args:
        max_results (int, optional): Maximum number of emails to fetch. 
                                   If None, fetches all available emails.
    
    Returns:
        int: Number of emails processed
    """
    # Initialize Gmail API service and database
    service = get_gmail_service()
    engine, Session = init_db()

    if not service or not Session:
        logger.error("Failed to initialize Gmail service or database")
        return 0

    try:
        # Create database session
        session = Session()
        processed_count = 0
        
        # Prepare the API request
        request_params = {
            'userId': 'me',
            'labelIds': ['INBOX']
        }
        
        # Add maxResults parameter if specified
        if max_results is not None:
            request_params['maxResults'] = max_results
            logger.info(f"Fetching up to {max_results} emails...")
        else:
            logger.info("Fetching all available emails...")
        
        # Fetch emails from Gmail API
        results = service.users().messages().list(**request_params).execute()
        messages = results.get('messages', [])
        
        # If fetching all emails, continue fetching until no more pages
        if max_results is None:
            while 'nextPageToken' in results:
                request_params['pageToken'] = results['nextPageToken']
                results = service.users().messages().list(**request_params).execute()
                messages.extend(results.get('messages', []))
        
        logger.info(f"Found {len(messages)} emails to process")
        
        for message in messages:
            # Get full message details
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()
            # Parse headers
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            to = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            date_received = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            # Get message body
            if 'data' in msg['payload'].get('body', {}):
                body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode()
            else:
                # Handle multipart messages
                raw_body = msg['payload']['parts'][0]['body'].get('data', '') if 'parts' in msg['payload'] and msg['payload']['parts'] else ''
                body = base64.urlsafe_b64decode(raw_body).decode() if raw_body else ''
            # Create Email object
            email_obj = Email(
                id=msg['id'],
                sender=sender,
                to=to,
                subject=subject,
                body=body,
                received=parse_email_date(date_received),
                is_read='UNREAD' not in msg['labelIds']
            )
            # Add to database
            try:
                session.merge(email_obj)
                processed_count += 1
                if processed_count % 10 == 0:  # Log progress every 10 emails
                    logger.info(f"Processed {processed_count} emails...")
            except Exception as e:
                logger.error(f"Error storing email {msg['id']}: {e}")
                continue
        # Commit after all emails
        session.commit()
        logger.success(f"Successfully processed {processed_count} emails")
        return processed_count
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        return 0
    finally:
        session.close()

if __name__ == '__main__':
    # Prompt user for email fetching preference
    print("\n" + "="*50)
    print("Gmail Email Fetcher")
    print("="*50)
    print("Choose an option:")
    print("1. Fetch only 10 most recent emails (recommended for testing)")
    print("2. Fetch all available emails (may take longer)")
    print("="*50)
    
    while True:
        try:
            choice = input("Enter your choice (1 or 2): ").strip()
            if choice == '1':
                logger.info("Fetching 10 most recent emails...")
                count = fetch_and_store_emails(max_results=10)
                break
            elif choice == '2':
                logger.info("Fetching all available emails...")
                count = fetch_and_store_emails(max_results=None)
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            exit(0)
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")
    
    if count > 0:
        logger.success(f"Successfully fetched and stored {count} emails")
    else:
        logger.error("Failed to fetch and store emails")