# Gmail Rule-Based Email Processor

A Python application that integrates with Gmail API to fetch emails, store them in a SQLite database, and process them using customizable rules.

## Features

- Gmail API integration using OAuth 2.0
- Local SQLite database storage for emails
- Customizable rule-based email processing
- Support for multiple actions (mark as read/unread, apply labels, archive, star, trash)
- Interactive command-line interface with email count options
- Comprehensive test coverage
- Progress tracking for large operations

## Prerequisites

- Python 3.7 or higher
- Google Cloud Platform account
- Gmail API enabled
- OAuth 2.0 credentials

## Setup

1. **Create Virtual Environment**

```bash
python3 -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up Google Cloud Project and OAuth Credentials**

- Go to [Google Cloud Console](https://console.cloud.google.com)
- Create a new project or select an existing one
- Enable the Gmail API for your project
- Configure the OAuth consent screen
- Create OAuth 2.0 credentials (Desktop application)
- Download the credentials and save as `credentials.json` in the project root

## Quick Start

1. **Clone and Setup**
```bash
git clone <repository-url>
cd gmail-rule-processor

# Create and activate virtual environment
python3 -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Add Credentials**
- Place your `credentials.json` file in the project root

3. **Authenticate with Gmail**
```bash
python auth.py
```
This will open a browser window for OAuth authentication. Complete the authentication flow.

4. **Initialize and Run**
```bash
python models.py                    # Initialize database
python fetch_emails.py              # Fetch emails (choose option 1 for testing)
python process_rules.py             # Process rules (choose option 1 for testing)
```

## Project Structure

```
├── auth.py              # Gmail API authentication
├── fetch_emails.py      # Email fetching and storage
├── models.py            # Database models
├── process_rules.py     # Rule processing engine
├── rules.json           # Rule definitions
├── test_rules.py        # Unit tests
├── requirements.txt     # Project dependencies
└── README.md           # This file
```

## Usage

1. **Initialize the Database**

```bash
python3 models.py
```

2. **Fetch Emails**

```bash
python3 fetch_emails.py
```

The script will prompt you to choose:
- **Option 1**: Fetch only 10 most recent emails (recommended for testing)
- **Option 2**: Fetch all available emails (may take longer)

3. **Process Rules**

```bash
python3 process_rules.py
```

The script will prompt you to choose:
- **Option 1**: Process only 10 most recent emails (recommended for testing)
- **Option 2**: Process all emails in database (may take longer)

## Rules Configuration

Rules are defined in `rules.json`. Each rule consists of conditions and actions.

### Example Rule Structure

```json
{
    "rules": [
        {
            "name": "Important Notifications",
            "conditions": {
                "predicate": "Any",
                "rules": [
                    {
                        "field": "From",
                        "predicate": "Contains",
                        "value": "notifications@github.com"
                    }
                ]
            },
            "actions": [
                {
                    "type": "mark_as_read",
                    "params": {}
                },
                {
                    "type": "move_message",
                    "params": {
                        "label": "Important"
                    }
                }
            ]
        }
    ]
}
```

### Current Rules

The following rules are currently configured in `rules.json`:

#### 1. **Mark as Read Example**
- **Condition**: From field contains 'satrajithrs@gmail.com'
- **Action**: Mark email as read
- **Purpose**: Automatically mark emails from specific sender as read

#### 2. **Move to Spam Example**
- **Condition**: From field contains '1by22ai083@bmsit.in'
- **Action**: Apply 'Spam' label
- **Purpose**: Automatically label emails from specific sender as spam

#### 3. **Starred Message Example**
- **Condition**: Subject contains 'Important'
- **Action**: Add star to email
- **Purpose**: Automatically star emails with 'Important' in subject

#### 4. **Label the Message Example**
- **Condition**: Subject contains 'Project'
- **Action**: Apply 'Work' label
- **Purpose**: Automatically label work-related emails

#### 5. **Move to Trash Example**
- **Condition**: Subject contains 'Spam Offer'
- **Action**: Move email to trash
- **Purpose**: Automatically delete spam offer emails

#### 6. **Mark as Unread and Archive**
- **Condition**: Subject contains 'Mark as unread'
- **Action**: Mark as unread AND archive
- **Purpose**: Mark specific emails as unread and remove from inbox

### Available Fields
- From
- Subject
- Message
- Received

### Available Predicates
- Contains
- Does not Contain
- Equals
- Does not Equal
- Less Than (for dates)
- Greater Than (for dates)

### Available Actions
- mark_as_read
- mark_as_unread
- add_star
- remove_star
- move_message (applies Gmail label)
- move_to_trash
- archive_message (removes from inbox)

## Database Management

The application uses a local SQLite database (`emails.db`) to store email data.

### Database Location
- **File**: `emails.db` in the project root
- **Size**: Grows based on number of emails fetched
- **Backup**: Consider backing up this file regularly

### Database Operations
- **Initialize**: Run `python3 models.py` to create tables
- **Reset**: Delete `emails.db` and re-run `python3 models.py`
- **Inspect**: Use SQLite tools to view data:
  ```bash
  sqlite3 emails.db
  .tables                    # Show tables
  SELECT COUNT(*) FROM emails;  # Count emails
  .quit                      # Exit
  ```

### Email Storage
- Emails are stored with full content (headers, body, metadata)
- Database uses `session.merge()` to avoid duplicates
- Email IDs from Gmail are used as primary keys

## API Quotas and Limits

### Gmail API Quotas
- **Daily quota**: 1 billion queries per day per project
- **Per-user rate limit**: 250 queries per second per user
- **Batch requests**: Up to 100 requests per batch

### Best Practices
- Use option 1 (10 emails) for testing to avoid quota issues
- Process emails in batches for large operations
- Monitor quota usage in Google Cloud Console
- Consider implementing exponential backoff for rate limiting

## Running Tests

```bash
python3 -m pytest test_rules.py -v
```

## Error Handling

The application uses the `loguru` library for logging. Check the console output for any errors during execution.

## Troubleshooting

### Common Issues

#### Authentication Errors
```
Error in OAuth flow: [Errno 2] No such file or directory: 'credentials.json'
```
**Solution**: Ensure `credentials.json` is in the project root directory

#### API Quota Exceeded
```
Quota exceeded for quota group 'default'
```
**Solution**: Wait for quota reset or use option 1 (10 emails) for testing

#### Database Errors
```
Error initializing database: [Errno 13] Permission denied
```
**Solution**: Check file permissions on `emails.db` and project directory

#### Gmail API Errors
```
Error fetching emails: 403 Forbidden
```
**Solution**: 
- Verify Gmail API is enabled in Google Cloud Console
- Check OAuth consent screen configuration
- Ensure credentials have correct scopes

### Debug Mode
Enable verbose logging by modifying the loguru configuration in any script:
```python
from loguru import logger
logger.add("debug.log", level="DEBUG")
```

### Reset Everything
To start fresh:
```bash
rm -f emails.db token.pickle
python3 models.py
# Re-authenticate when prompted
```

## Security Notes

- Keep your `credentials.json` file secure and never commit it to version control
- The application stores OAuth tokens in `token.pickle` - keep this file secure as well
- The SQLite database file contains email content - ensure appropriate file permissions
- Consider encrypting the database file for additional security
- Regularly rotate OAuth credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

##Video Demonstration Link
https://drive.google.com/file/d/1Vvs4SoqpFJFjNU3FQ7DwRftkPP9wgqtX/view?usp=sharing
