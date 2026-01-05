import json
import os
import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

class FilterService:
    """
    Manages email filtering rules (ignore lists).
    Persists rules to filters_config.json.
    """
    
    def __init__(self, config_file: str = "filters_config.json"):
        self.config_file = config_file
        self.ignored_senders: Set[str] = set()
        self.ignored_subjects: Set[str] = set()
        self._load_filters()

    def _load_filters(self):
        """Load filters from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.ignored_senders = set(data.get("ignored_senders", []))
                    self.ignored_subjects = set(data.get("ignored_subjects", []))
                logger.info(f"Loaded filters: {len(self.ignored_senders)} senders, {len(self.ignored_subjects)} subjects")
            else:
                logger.info("No filter config found, starting with empty filters")
        except Exception as e:
            logger.error(f"Error loading filters: {e}")

    def _save_filters(self):
        """Save filters to JSON file"""
        try:
            data = {
                "ignored_senders": list(self.ignored_senders),
                "ignored_subjects": list(self.ignored_subjects)
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=4)
            logger.info("Filters saved to disk")
        except Exception as e:
            logger.error(f"Error saving filters: {e}")

    def should_process(self, email_data) -> bool:
        """
        Check if email should be processed or skipped.
        Returns True if email should be processed, False if it should be skipped.
        """
        # Check sender
        sender = email_data.sender.lower() if email_data.sender else ""
        for ignored in self.ignored_senders:
            if ignored.lower() in sender:
                logger.info(f"Skipping email from ignored sender: {sender} (matched '{ignored}')")
                return False

        # Check subject
        subject = email_data.subject.lower() if email_data.subject else ""
        for ignored in self.ignored_subjects:
            if ignored.lower() in subject:
                logger.info(f"Skipping email with ignored subject content: {subject} (matched '{ignored}')")
                return False

        return True

    def add_ignore_sender(self, sender: str) -> bool:
        """Add sender to ignore list"""
        if sender and sender not in self.ignored_senders:
            self.ignored_senders.add(sender)
            self._save_filters()
            return True
        return False

    def remove_ignore_sender(self, sender: str) -> bool:
        """Remove sender from ignore list"""
        if sender in self.ignored_senders:
            self.ignored_senders.remove(sender)
            self._save_filters()
            return True
        return False

    def add_ignore_subject(self, keyword: str) -> bool:
        """Add subject keyword to ignore list"""
        if keyword and keyword not in self.ignored_subjects:
            self.ignored_subjects.add(keyword)
            self._save_filters()
            return True
        return False

    def remove_ignore_subject(self, keyword: str) -> bool:
        """Remove subject keyword from ignore list"""
        if keyword in self.ignored_subjects:
            self.ignored_subjects.remove(keyword)
            self._save_filters()
            return True
        return False

    def get_filters(self) -> Dict[str, List[str]]:
        """Get all active filters"""
        return {
            "ignored_senders": list(self.ignored_senders),
            "ignored_subjects": list(self.ignored_subjects)
        }
