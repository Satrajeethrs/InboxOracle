#!/usr/bin/env python3

import unittest
from datetime import datetime
from models import Email
from process_rules import RuleProcessor
from unittest.mock import MagicMock, patch, create_autospec

class TestRuleProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.processor = RuleProcessor()
        self.test_email = Email(
            id='test123',
            sender='test@example.com',
            subject='Test Subject',
            body='Test message body',
            received=datetime(2023, 1, 1, 12, 0, 0),
            is_read=False
        )

    def test_condition_contains(self):
        """Test 'Contains' predicate"""
        condition = {
            'field': 'Subject',
            'predicate': 'Contains',
            'value': 'Test'
        }
        self.assertTrue(self.processor._evaluate_condition(self.test_email, condition))

    def test_condition_does_not_contain(self):
        """Test 'Does not Contain' predicate"""
        condition = {
            'field': 'Subject',
            'predicate': 'Does not Contain',
            'value': 'Newsletter'
        }
        self.assertTrue(self.processor._evaluate_condition(self.test_email, condition))

    def test_condition_equals(self):
        """Test 'Equals' predicate"""
        condition = {
            'field': 'Subject',
            'predicate': 'Equals',
            'value': 'Test Subject'
        }
        self.assertTrue(self.processor._evaluate_condition(self.test_email, condition))

    def test_date_comparison(self):
        """Test date comparison predicates"""
        condition = {
            'field': 'Received',
            'predicate': 'Greater Than',
            'value': '2022-12-31T00:00:00Z'
        }
        self.assertTrue(self.processor._evaluate_condition(self.test_email, condition))

    def test_all_predicate(self):
        """Test 'All' predicate with multiple conditions"""
        rule_conditions = {
            'predicate': 'All',
            'rules': [
                {
                    'field': 'Subject',
                    'predicate': 'Contains',
                    'value': 'Test'
                },
                {
                    'field': 'From',
                    'predicate': 'Contains',
                    'value': 'example.com'
                }
            ]
        }
        self.assertTrue(self.processor._evaluate_rule_conditions(self.test_email, rule_conditions))

    def test_any_predicate(self):
        """Test 'Any' predicate with multiple conditions"""
        rule_conditions = {
            'predicate': 'Any',
            'rules': [
                {
                    'field': 'Subject',
                    'predicate': 'Contains',
                    'value': 'NonExistent'
                },
                {
                    'field': 'From',
                    'predicate': 'Contains',
                    'value': 'example.com'
                }
            ]
        }
        self.assertTrue(self.processor._evaluate_rule_conditions(self.test_email, rule_conditions))

    def test_mark_as_read_action(self):
        """Test 'mark_as_read' action"""
        # Create a mock service with autospec
        mock_service = create_autospec(self.processor.gmail_service)
        self.processor.gmail_service = mock_service

        # Set up the mock chain
        mock_modify = mock_service.users().messages().modify
        mock_modify.return_value.execute = MagicMock()

        # Test action
        action = {'type': 'mark_as_read', 'params': {}}
        self.processor._apply_action('test123', action)

        # Verify service chain was called correctly
        mock_modify.assert_called_with(
            userId='me',
            id='test123',
            body={'removeLabelIds': ['UNREAD']}
        )
        mock_modify.return_value.execute.assert_called_once()

    def test_move_message_action(self):
        """Test 'move_message' action"""
        # Create a mock service with autospec
        mock_service = create_autospec(self.processor.gmail_service)
        self.processor.gmail_service = mock_service

        # Mock label list response
        mock_service.users().labels().list().execute.return_value = {
            'labels': [{'id': 'Label_1', 'name': 'Important'}]
        }

        # Set up the mock chain
        mock_modify = mock_service.users().messages().modify
        mock_modify.return_value.execute = MagicMock()

        # Test action
        action = {
            'type': 'move_message',
            'params': {'label': 'Important'}
        }
        self.processor._apply_action('test123', action)

        # Verify service chain was called correctly
        mock_modify.assert_called_with(
            userId='me',
            id='test123',
            body={'addLabelIds': ['Label_1']}
        )
        mock_modify.return_value.execute.assert_called_once()

    def test_archive_message_action(self):
        """Test 'archive_message' action"""
        # Create a mock service with autospec
        mock_service = create_autospec(self.processor.gmail_service)
        self.processor.gmail_service = mock_service

        # Set up the mock chain
        mock_modify = mock_service.users().messages().modify
        mock_modify.return_value.execute = MagicMock()

        # Test action
        action = {'type': 'archive_message', 'params': {}}
        self.processor._apply_action('test123', action)

        # Verify service chain was called correctly
        mock_modify.assert_called_with(
            userId='me',
            id='test123',
            body={'removeLabelIds': ['INBOX']}
        )
        mock_modify.return_value.execute.assert_called_once()

if __name__ == '__main__':
    unittest.main()