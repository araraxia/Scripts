#!/usr/bin/env python3
"""
Print Thread Messages Script

This script retrieves a Gmail thread by its thread ID and prints the full body
of each message in the thread to the terminal.

Usage:
    python print_thread_messages.py <thread_id>
    python print_thread_messages.py <thread_id> --user user@example.com
    python print_thread_messages.py <thread_id> --show-headers
    python print_thread_messages.py <thread_id> --html

Arguments:
    thread_id: The Gmail thread ID (required)
    --user: Email address to impersonate (default: no-reply@example.com)
    --show-headers: Display all email headers
    --html: Display HTML body instead of plain text (when available)
    --no-color: Disable colored output

Examples:
    # Print messages from a thread
    python print_thread_messages.py 18c5a1b2f3d4e5f6

    # Print with all headers
    python print_thread_messages.py 18c5a1b2f3d4e5f6 --show-headers

    # Access different user's thread
    python print_thread_messages.py 18c5a1b2f3d4e5f6 --user support@example.com
"""

from pathlib import Path
import os
import sys
import argparse
from datetime import datetime

# Setup path
ROOT = Path(__file__).resolve().parent.parent.parent  # /menoapi
src_path = ROOT / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from extras.service_account_email_manager import ServiceAccountEmailManager

# Default credentials
CRED_DIR = ROOT / "cred"
NOREPLY_SA = CRED_DIR / "noreply_sa.json"


# ANSI color codes
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"

    @classmethod
    def disable(cls):
        """Disable all colors."""
        cls.HEADER = ""
        cls.BLUE = ""
        cls.CYAN = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.RED = ""
        cls.BOLD = ""
        cls.UNDERLINE = ""
        cls.END = ""


def print_separator(char="═", length=80, color=None):
    """Print a separator line."""
    line = char * length
    if color:
        print(f"{color}{line}{Colors.END}")
    else:
        print(line)


def print_header(text, color=None):
    """Print a formatted header."""
    if color:
        print(f"\n{color}{Colors.BOLD}{text}{Colors.END}")
    else:
        print(f"\n{text}")
    print_separator("─", length=len(text))


def format_message_header(message, index, total):
    """Format message header information."""
    lines = []
    lines.append("")
    print_separator("═", color=Colors.CYAN)
    lines.append(f"{Colors.BOLD}MESSAGE {index}/{total}{Colors.END}")
    print_separator("═", color=Colors.CYAN)

    lines.append(f"{Colors.BOLD}Message ID:{Colors.END} {message.id}")
    lines.append(f"{Colors.BOLD}From:{Colors.END} {message.from_email}")
    lines.append(f"{Colors.BOLD}To:{Colors.END} {message.to_email}")

    if message.cc_email:
        lines.append(f"{Colors.BOLD}CC:{Colors.END} {message.cc_email}")

    if message.bcc_email:
        lines.append(f"{Colors.BOLD}BCC:{Colors.END} {message.bcc_email}")

    lines.append(f"{Colors.BOLD}Subject:{Colors.END} {message.subject}")
    lines.append(f"{Colors.BOLD}Date:{Colors.END} {message.date}")

    # Status indicators
    status = []
    if message.is_unread():
        status.append(f"{Colors.YELLOW}UNREAD{Colors.END}")
    if message.is_starred():
        status.append(f"{Colors.YELLOW}STARRED{Colors.END}")
    if message.is_important():
        status.append(f"{Colors.RED}IMPORTANT{Colors.END}")
    if message.has_attachments():
        attachments = message.get_attachments()
        status.append(f"{Colors.GREEN}{len(attachments)} ATTACHMENT(S){Colors.END}")

    if status:
        lines.append(f"{Colors.BOLD}Status:{Colors.END} {', '.join(status)}")

    # Labels
    if message.label_ids:
        labels = [
            f"{Colors.BLUE}{label}{Colors.END}"
            for label in message.label_ids
            if label
            not in [
                "UNREAD",
                "CATEGORY_PERSONAL",
                "CATEGORY_SOCIAL",
                "CATEGORY_UPDATES",
                "CATEGORY_FORUMS",
                "CATEGORY_PROMOTIONS",
            ]
        ]
        if labels:
            lines.append(f"{Colors.BOLD}Labels:{Colors.END} {', '.join(labels)}")

    # Attachments details
    if message.has_attachments():
        lines.append(f"\n{Colors.BOLD}Attachments:{Colors.END}")
        for att in message.get_attachments():
            size_kb = att["size"] / 1024
            lines.append(
                f"  • {Colors.GREEN}{att['filename']}{Colors.END} ({size_kb:.2f} KB, {att['mimeType']})"
            )

    return "\n".join(lines)


def format_all_headers(message):
    """Format all email headers."""
    lines = []
    lines.append(f"\n{Colors.BOLD}{Colors.UNDERLINE}All Headers:{Colors.END}")

    for header_name, header_value in message.headers.items():
        lines.append(f"{Colors.CYAN}{header_name}:{Colors.END} {header_value}")

    return "\n".join(lines)


def format_message_body(body, max_width=100):
    """Format message body for display."""
    if not body:
        return f"{Colors.YELLOW}[No body content]{Colors.END}"

    # Clean up excessive newlines
    lines = body.split("\n")
    cleaned_lines = []
    empty_count = 0

    for line in lines:
        if not line.strip():
            empty_count += 1
            if empty_count <= 2:  # Allow max 2 consecutive empty lines
                cleaned_lines.append(line)
        else:
            empty_count = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def print_thread_messages(
    thread_id, user_email, show_headers=False, show_html=False, use_color=True
):
    """Retrieve and print all messages in a thread."""

    if not use_color:
        Colors.disable()

    # Initialize email manager
    print(f"{Colors.CYAN}Initializing email manager...{Colors.END}")
    if user_email:
        print(f"{Colors.CYAN}Accessing mailbox: {user_email}{Colors.END}")

    manager = ServiceAccountEmailManager(
        service_account_file=str(NOREPLY_SA), impersonate_user=user_email
    )

    # Get thread
    print(f"{Colors.CYAN}Retrieving thread: {thread_id}{Colors.END}\n")

    try:
        thread = manager.get_thread_by_id(thread_id, user_email="me")

        if not thread:
            print(f"{Colors.RED}❌ Thread not found: {thread_id}{Colors.END}")
            return

        # Print thread overview
        print_separator("═", color=Colors.HEADER)
        print(f"{Colors.BOLD}{Colors.HEADER}THREAD OVERVIEW{Colors.END}")
        print_separator("═", color=Colors.HEADER)
        print(f"{Colors.BOLD}Thread ID:{Colors.END} {thread.id}")
        print(f"{Colors.BOLD}Subject:{Colors.END} {thread.subject}")
        print(f"{Colors.BOLD}Messages:{Colors.END} {thread.message_count}")
        print(
            f"{Colors.BOLD}Participants:{Colors.END} {', '.join(thread.participants)}"
        )

        thread_status = []
        if thread.has_unread:
            thread_status.append(f"{Colors.YELLOW}HAS UNREAD{Colors.END}")
        if thread.has_starred:
            thread_status.append(f"{Colors.YELLOW}HAS STARRED{Colors.END}")

        if thread_status:
            print(f"{Colors.BOLD}Thread Status:{Colors.END} {', '.join(thread_status)}")

        print_separator("═", color=Colors.HEADER)

        # Print each message
        for i, message in enumerate(thread.messages, 1):
            print(format_message_header(message, i, thread.message_count))

            if show_headers:
                print(format_all_headers(message))

            # Print message body
            print(f"\n{Colors.BOLD}{Colors.UNDERLINE}Message Body:{Colors.END}\n")
            body = message.body
            print(format_message_body(body))
            print("")

        # Summary
        print_separator("═", color=Colors.GREEN)
        print(
            f"{Colors.GREEN}{Colors.BOLD}✓ Successfully displayed {thread.message_count} message(s) from thread {thread_id}{Colors.END}"
        )
        print_separator("═", color=Colors.GREEN)

    except Exception as e:
        print(f"\n{Colors.RED}❌ ERROR: {e}{Colors.END}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Print full message bodies from a Gmail thread",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 18c5a1b2f3d4e5f6
  %(prog)s 18c5a1b2f3d4e5f6 --show-headers
  %(prog)s 18c5a1b2f3d4e5f6 --user support@example.com
  %(prog)s 18c5a1b2f3d4e5f6 --no-color > output.txt
        """,
    )

    parser.add_argument("thread_id", help="Gmail thread ID to retrieve")

    parser.add_argument(
        "--user",
        help="Email address to impersonate (default: no-reply@example.com)",
    )

    parser.add_argument(
        "--show-headers",
        action="store_true",
        help="Display all email headers for each message",
    )

    parser.add_argument(
        "--html",
        action="store_true",
        help="Display HTML body instead of plain text (when available)",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output (useful for piping to file)",
    )

    args = parser.parse_args()

    # Use default user if not specified
    user_email = args.user if args.user else "no-reply@example.com"

    # Print thread messages
    print_thread_messages(
        thread_id=args.thread_id,
        user_email=user_email,
        show_headers=args.show_headers,
        show_html=args.html,
        use_color=not args.no_color,
    )


if __name__ == "__main__":
    main()
