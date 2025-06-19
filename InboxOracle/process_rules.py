#!/usr/bin/env python3

from auth import get_gmail_service
from models import Email, init_db
from datetime import datetime, timezone
from loguru import logger
import json
import dateutil.parser

class RuleProcessor:
    def __init__(self, rules_file='rules.json'):
        """Initialize RuleProcessor with rules file and Gmail service"""
        self.gmail_service = get_gmail_service()
        self.rules = self._load_rules(rules_file)
        engine, Session = init_db()
        if Session is None:
            raise RuntimeError("Database session could not be initialized.")
        self.session = Session()

    def _load_rules(self, rules_file):
        """Load rules from JSON file"""
        try:
            with open(rules_file, 'r') as f:
                return json.load(f)['rules']
        except Exception as e:
            logger.error(f"Error loading rules file: {e}")
            return []

    def _evaluate_condition(self, email, condition):
        """Evaluate a single condition against an email"""
        field = condition['field']
        predicate = condition['predicate']
        value = condition['value']

        if field == 'From':
            field_value = email.sender
        elif field == 'To':
            field_value = email.to
        elif field == 'Subject':
            field_value = email.subject
        elif field == 'Message':
            field_value = email.body
        elif field == 'Received':
            field_value = email.received.replace(tzinfo=timezone.utc)
            value = dateutil.parser.parse(value)
        else:
            return False

        if predicate == 'Contains':
            return str(value).lower() in str(field_value).lower()
        elif predicate == 'Does not Contain':
            return str(value).lower() not in str(field_value).lower()
        elif predicate == 'Equals':
            if isinstance(field_value, str) and isinstance(value, str):
                return field_value.lower() == value.lower()
            else:
                return field_value == value
        elif predicate == 'Does not Equal':
            if isinstance(field_value, str) and isinstance(value, str):
                return field_value.lower() != value.lower()
            else:
                return field_value != value
        elif predicate == 'Less Than' and isinstance(field_value, datetime):
            return field_value < value
        elif predicate == 'Greater Than' and isinstance(field_value, datetime):
            return field_value > value
        return False

    def _evaluate_rule_conditions(self, email, rule_conditions):
        """Evaluate all conditions in a rule"""
        predicate = rule_conditions['predicate']
        conditions = rule_conditions['rules']

        results = [self._evaluate_condition(email, condition) for condition in conditions]

        if predicate == 'All':
            return all(results)
        elif predicate == 'Any':
            return any(results)
        return False

    def _apply_action(self, email_id, action):
        """Apply a single action to an email"""
        action_type = action['type']
        try:
            if self.gmail_service is None:
                logger.error("Gmail service is not initialized.")
                return
            if action_type == 'mark_as_read':
                self.gmail_service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                # Update local DB
                email_obj = self.session.query(Email).filter_by(id=email_id).first()
                if email_obj:
                    email_obj.is_read = True
                    self.session.commit()
                logger.info(f"Marked email {email_id} as read")

            elif action_type == 'mark_as_unread':
                self.gmail_service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body={'addLabelIds': ['UNREAD']}
                ).execute()
                # Update local DB
                email_obj = self.session.query(Email).filter_by(id=email_id).first()
                if email_obj:
                    email_obj.is_read = False
                    self.session.commit()
                logger.info(f"Marked email {email_id} as unread")

            elif action_type == 'add_star':
                self.gmail_service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body={'addLabelIds': ['STARRED']}
                ).execute()
                logger.info(f"Marked email {email_id} as starred")

            elif action_type == 'remove_star':
                self.gmail_service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body={'removeLabelIds': ['STARRED']}
                ).execute()
                logger.info(f"Removed star from email {email_id}")

            elif action_type == 'move_message':
                label_name = action['params']['label']
                # Create label if it doesn't exist
                try:
                    label_list = self.gmail_service.users().labels().list(userId='me').execute()
                    label = next((label for label in label_list['labels'] 
                                if label['name'].lower() == label_name.lower()), None)
                    
                    if not label:
                        label = self.gmail_service.users().labels().create(
                            userId='me',
                            body={'name': label_name}
                        ).execute()
                        logger.info(f"Created new label: {label_name}")
                    
                    # Apply label
                    self.gmail_service.users().messages().modify(
                        userId='me',
                        id=email_id,
                        body={'addLabelIds': [label['id']]}
                    ).execute()
                    logger.info(f"Applied label {label_name} to email {email_id}")
                    
                except Exception as e:
                    logger.error(f"Error applying label {label_name} to email {email_id}: {e}")

            elif action_type == 'move_to_trash':
                self.gmail_service.users().messages().trash(
                    userId='me',
                    id=email_id
                ).execute()
                logger.info(f"Moved email {email_id} to Trash")

            elif action_type == 'archive_message':
                self.gmail_service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body={'removeLabelIds': ['INBOX']}
                ).execute()
                logger.info(f"Archived email {email_id}")

        except Exception as e:
            logger.error(f"Error applying action {action_type} to email {email_id}: {e}")

    def process_emails(self, limit=None):
        """
        Process emails against rules
        
        Args:
            limit (int, optional): Maximum number of emails to process. 
                                 If None, processes all emails in database.
        """
        try:
            # Build query for emails
            query = self.session.query(Email).order_by(Email.received.desc())
            
            if limit is not None:
                query = query.limit(limit)
                logger.info(f"Processing {limit} most recent emails against {len(self.rules)} rules")
            else:
                logger.info(f"Processing all emails against {len(self.rules)} rules")
            
            emails = query.all()
            logger.info(f"Found {len(emails)} emails to process")

            processed_count = 0
            for email in emails:
                for rule in self.rules:
                    if self._evaluate_rule_conditions(email, rule['conditions']):
                        logger.info(f"Rule '{rule['name']}' matched email {email.id}")
                        for action in rule['actions']:
                            self._apply_action(email.id, action)
                processed_count += 1
                if processed_count % 10 == 0:  # Log progress every 10 emails
                    logger.info(f"Processed {processed_count} emails...")

            logger.success(f"Completed processing {processed_count} emails")

        except Exception as e:
            logger.error(f"Error processing emails: {e}")

        finally:
            self.session.close()

if __name__ == '__main__':
    # Prompt user for email processing preference
    print("\n" + "="*50)
    print("Gmail Rule Processor")
    print("="*50)
    print("Choose an option:")
    print("1. Process only 10 most recent emails (recommended for testing)")
    print("2. Process all emails in database (may take longer)")
    print("="*50)
    
    while True:
        try:
            choice = input("Enter your choice (1 or 2): ").strip()
            if choice == '1':
                logger.info("Processing 10 most recent emails...")
                processor = RuleProcessor()
                processor.process_emails(limit=10)
                break
            elif choice == '2':
                logger.info("Processing all emails...")
                processor = RuleProcessor()
                processor.process_emails(limit=None)
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            exit(0)
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")