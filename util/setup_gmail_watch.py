#!/usr/bin/env python3
"""
Setup Gmail Watch Script

This script initializes ServiceAccountEmailManager with the PTS CSR email
and sets up Gmail push notifications to monitor incoming emails.

The watch will monitor all mailbox changes and send notifications to the
configured Pub/Sub topic (PTS_CSR_TOPIC_NAME from .env).

Usage:
    python src/scripts/setup_gmail_watch.py

Requirements:
    - PTS_CSR_EMAIL set in .env
    - PTS_CSR_TOPIC_NAME set in .env
    - Service account with domain-wide delegation
    - Pub/Sub topic with permissions for gmail-api-push@system.gserviceaccount.com
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directories to path for imports
FILE_PATH = Path(__file__).resolve()
ROOT_PATH = FILE_PATH.parent.parent.parent
sys.path.insert(0, str(ROOT_PATH))

# Load environment variables
load_dotenv()

from src.extras.service_account_email_manager import ServiceAccountEmailManager


def setup_gmail_watch():
    """
    Initialize ServiceAccountEmailManager and set up Gmail watch.

    Returns:
        dict: Watch response with historyId and expiration
    """
    # Get configuration from environment
    pts_csr_email = os.getenv("PTS_CSR_EMAIL")
    pts_csr_topic = os.getenv("PTS_CSR_TOPIC_NAME")

    # Validate configuration
    if not pts_csr_email:
        raise ValueError(
            "PTS_CSR_EMAIL environment variable is not set. "
            "Please add it to your .env file."
        )

    if not pts_csr_topic:
        raise ValueError(
            "PTS_CSR_TOPIC_NAME environment variable is not set. "
            "Please add it to your .env file."
        )

    print(f"Initializing ServiceAccountEmailManager...")
    print(f"  Impersonating: {pts_csr_email}")
    print(f"  Pub/Sub Topic: {pts_csr_topic}")

    # Initialize email manager
    manager = ServiceAccountEmailManager(impersonate_user=pts_csr_email)

    print(f"\nSetting up Gmail watch...")

    # Set up watch (uses PTS_CSR_TOPIC_NAME from .env by default)
    response = manager.watch()

    # Parse expiration timestamp (in milliseconds)
    expiration_ms = int(response["expiration"])
    expiration_dt = datetime.fromtimestamp(expiration_ms / 1000)

    print(f"\n[OK] Gmail watch setup successful!")
    print(f"  History ID: {response['historyId']}")
    print(f"  Expiration: {expiration_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Expires in: ~7 days")
    print(f"\nGmail will now send push notifications to:")
    print(f"  {pts_csr_topic}")
    print(f"\nNote: Remember to renew the watch before it expires!")

    return response


def main():
    """Main entry point for the script."""
    try:
        response = setup_gmail_watch()
        return 0
    except ValueError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"File Error: {e}", file=sys.stderr)
        print("\nMake sure the service account file exists at:", file=sys.stderr)
        print("  cred/meno_api_service_account.json", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nTroubleshooting tips:", file=sys.stderr)
        print(
            "  1. Ensure domain-wide delegation is enabled for the service account",
            file=sys.stderr,
        )
        print(
            "  2. Verify Gmail API scopes are authorized in Google Workspace Admin",
            file=sys.stderr,
        )
        print(
            "  3. Check that the Pub/Sub topic has permissions for gmail-api-push@system.gserviceaccount.com",
            file=sys.stderr,
        )
        print(
            "  4. Confirm the PTS_CSR_EMAIL user exists in your workspace",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
