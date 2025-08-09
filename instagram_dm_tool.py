#!/usr/bin/env python3
"""
instagram_dm_tool.py
Instagram DM tool with PROPER PAGINATION using Instagram's cursor system.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Check Python version
if sys.version_info < (3, 6):
    print("ERROR: Python 3.6 or higher required")
    sys.exit(1)

try:
    from instagrapi import Client
    print("✓ instagrapi imported successfully")
except ImportError as e:
    print(f"ERROR: instagrapi not installed: {e}")
    print("Install with: pip install instagrapi")
    sys.exit(1)

# Constants
SESSION_FILE = "session.json"

def get_password():
    """Get password input"""
    try:
        import getpass
        return getpass.getpass("Instagram password (hidden): ")
    except Exception:
        print("Note: Password will be visible")
        return input("Instagram password: ")

def load_session(client: Client, session_file: str) -> bool:
    """Load session"""
    if not os.path.exists(session_file):
        return False
    try:
        client.load_settings(session_file)
        client.account_info()
        return True
    except:
        try:
            os.remove(session_file)
        except:
            pass
        return False

def save_session(client: Client, session_file: str) -> bool:
    """Save session"""
    try:
        client.dump_settings(session_file)
        return True
    except:
        return False

class IGDMTool:
    def __init__(self):
        self.client = Client()
        self.logged_in = False
        self.selected_thread_id = None
        self.my_username = None
        self.my_user_id = None
        print("✓ IGDMTool initialized")
    
    def login(self):
        """Login to Instagram"""
        print("\n=== LOGIN ===")
        
        # Try existing session
        if load_session(self.client, SESSION_FILE):
            try:
                user_info = self.client.account_info()
                self.my_username = user_info.username
                self.my_user_id = str(user_info.pk)
                print(f"✓ Loaded session for: {self.my_username}")
                self.logged_in = True
                return True
            except:
                print("Session invalid")
        
        # Fresh login
        username = input("Instagram username: ").strip()
        if not username:
            return False
        
        password = get_password().strip()
        if not password:
            return False
        
        try:
            print("Logging in...")
            self.client.login(username, password)
            
            user_info = self.client.account_info()
            self.my_username = user_info.username
            self.my_user_id = str(user_info.pk)
            
            save_session(self.client, SESSION_FILE)
            print(f"✓ Logged in as: {self.my_username}")
            self.logged_in = True
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def list_threads_raw_api(self):
        """Use raw API call to get threads"""
        if not self.logged_in:
            print("Please login first")
            return False
        
        print("\n=== MESSAGE THREADS (RAW API) ===")
        
        try:
            print("Getting threads via raw API...")
            
            response = self.client.private_request("direct_v2/inbox/", params={
                "visual_message_return_type": "unseen",
                "thread_message_limit": "10",
                "persistentBadging": "true",
                "limit": "20"
            })
            
            if not response or 'inbox' not in response:
                print("No inbox data received")
                return False
            
            inbox = response['inbox']
            threads = inbox.get('threads', [])
            
            if not threads:
                print("No threads found")
                return False
            
            print(f"Found {len(threads)} threads:")
            print()
            
            for i, thread in enumerate(threads, 1):
                try:
                    thread_id = thread.get('thread_id', 'Unknown')
                    
                    # Get usernames
                    users = thread.get('users', [])
                    usernames = []
                    for user in users[:3]:
                        if 'username' in user:
                            usernames.append(user['username'])
                    
                    users_str = ", ".join(usernames) if usernames else "Unknown users"
                    
                    # Get last message
                    items = thread.get('items', [])
                    last_msg = ""
                    if items:
                        last_item = items[0]
                        if 'text' in last_item and last_item['text']:
                            last_msg = last_item['text'][:50]
                            if len(last_item['text']) > 50:
                                last_msg += "..."
                        else:
                            last_msg = "[Media/Other]"
                    
                    print(f"{i:2d}. ID: {thread_id}")
                    print(f"    Users: {users_str}")
                    print(f"    Last: {last_msg}")
                    print()
                    
                except Exception as e:
                    print(f"{i:2d}. [Error: {e}]")
                    continue
            
            # Let user select
            try:
                choice = input("Select thread number (or Enter to cancel): ").strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(threads):
                        self.selected_thread_id = threads[idx].get('thread_id')
                        print(f"✓ Selected thread: {self.selected_thread_id}")
                        return True
                    else:
                        print("Invalid selection")
            except:
                print("Invalid input")
            
            return False
            
        except Exception as e:
            print(f"Failed to list threads: {e}")
            return False
    
    def select_thread(self):
        """Select thread by ID or username"""
        if not self.logged_in:
            print("Please login first")
            return False
        
        print("\n=== SELECT THREAD ===")
        thread_input = input("Enter thread ID or username: ").strip()
        if not thread_input:
            return False
        
        try:
            if thread_input.isdigit():
                self.selected_thread_id = thread_input
                print(f"✓ Selected thread ID: {thread_input}")
                return True
            else:
                print(f"Looking up user: {thread_input}")
                user_id = self.client.user_id_from_username(thread_input)
                print(f"Found user ID: {user_id}")
                
                # Try to find thread via raw API
                response = self.client.private_request("direct_v2/inbox/", params={
                    "visual_message_return_type": "unseen",
                    "thread_message_limit": "10",
                    "persistentBadging": "true",
                    "limit": "50"
                })
                
                if response and 'inbox' in response:
                    threads = response['inbox'].get('threads', [])
                    for thread in threads:
                        users = thread.get('users', [])
                        for user in users:
                            if str(user.get('pk', '')) == str(user_id):
                                self.selected_thread_id = thread.get('thread_id')
                                print(f"✓ Found thread: {self.selected_thread_id}")
                                return True
                
                print("No thread found with that user")
                return False
        except Exception as e:
            print(f"Failed to select thread: {e}")
            return False
    
    def fetch_all_messages_paginated(self, max_messages=5000):
        """Fetch messages with PROPER Instagram pagination using cursors"""
        all_messages = []
        cursor = None
        page = 1
        consecutive_empty_pages = 0
        
        print(f"Fetching up to {max_messages} messages with PROPER pagination...")
        
        while len(all_messages) < max_messages and consecutive_empty_pages < 3:
            try:
                print(f"Fetching page {page}... (have {len(all_messages)} messages)")
                
                # Build params for pagination
                params = {
                    "visual_message_return_type": "unseen",
                    "direction": "older",
                    "limit": "75"  # Instagram's max per request
                }
                
                # Add cursor for pagination if we have one
                if cursor:
                    params["cursor"] = cursor
                
                response = self.client.private_request(
                    f"direct_v2/threads/{self.selected_thread_id}/", 
                    params=params
                )
                
                if not response or 'thread' not in response:
                    print(f"No response data on page {page}")
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= 3:
                        break
                    page += 1
                    time.sleep(1)
                    continue
                
                thread = response['thread']
                items = thread.get('items', [])
                
                if not items:
                    print(f"No items on page {page}")
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= 3:
                        print("No more messages found after 3 empty pages")
                        break
                    page += 1
                    time.sleep(1)
                    continue
                
                # Reset empty page counter since we got items
                consecutive_empty_pages = 0
                
                # Add new messages
                new_messages = 0
                for item in items:
                    if len(all_messages) >= max_messages:
                        break
                    all_messages.append(item)
                    new_messages += 1
                
                print(f"Page {page}: Got {new_messages} messages")
                
                # Get cursor for next page from the response
                # Instagram provides cursors in different places
                cursor = None
                
                # Method 1: Check thread-level cursor
                if 'oldest_cursor' in thread:
                    cursor = thread['oldest_cursor']
                    print(f"Using oldest_cursor: {cursor[:50]}...")
                
                # Method 2: Check if there's a next_cursor
                elif 'next_cursor' in thread:
                    cursor = thread['next_cursor']
                    print(f"Using next_cursor: {cursor[:50]}...")
                
                # Method 3: Use the last item's timestamp as cursor
                elif items:
                    last_item = items[-1]
                    if 'timestamp' in last_item:
                        cursor = str(last_item['timestamp'])
                        print(f"Using timestamp cursor: {cursor}")
                
                # Method 4: Check response-level pagination
                elif 'paging_info' in response:
                    paging = response['paging_info']
                    if 'max_id' in paging:
                        cursor = paging['max_id']
                        print(f"Using max_id cursor: {cursor}")
                
                # If no cursor found, try to continue anyway
                if not cursor and items:
                    # Use last item ID as fallback
                    last_item = items[-1]
                    cursor = (last_item.get('item_id') or 
                             last_item.get('id') or 
                             last_item.get('client_context'))
                    if cursor:
                        print(f"Using fallback cursor: {cursor}")
                
                # If still no cursor, we might be at the end
                if not cursor:
                    print("No cursor found - might be at end of messages")
                    # Try one more page without cursor
                    if page == 1:
                        page += 1
                        time.sleep(1)
                        continue
                    else:
                        break
                
                page += 1
                time.sleep(0.8)  # Slightly longer delay to avoid rate limits
                
            except Exception as e:
                print(f"Error on page {page}: {e}")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 3:
                    break
                page += 1
                time.sleep(2)  # Longer delay on error
        
        print(f"Total messages fetched: {len(all_messages)} across {page-1} pages")
        return all_messages
    
    def view_messages_raw_api(self):
        """View messages using raw API call"""
        if not self.logged_in:
            print("Please login first")
            return
        
        if not self.selected_thread_id:
            print("Please select a thread first")
            return
        
        print(f"\n=== MESSAGES IN THREAD {self.selected_thread_id} ===")
        
        try:
            amount = input("Number of messages (default 20): ").strip()
            amount = int(amount) if amount.isdigit() else 20
            
            if amount > 75:
                print(f"Using PROPER pagination to fetch {amount} messages...")
                items = self.fetch_all_messages_paginated(amount)
            else:
                print(f"Fetching {amount} messages...")
                response = self.client.private_request(f"direct_v2/threads/{self.selected_thread_id}/", params={
                    "visual_message_return_type": "unseen",
                    "direction": "older",
                    "limit": str(amount)
                })
                
                if not response or 'thread' not in response:
                    print("No thread data received")
                    return
                
                items = response['thread'].get('items', [])
            
            if not items:
                print("No messages found")
                return
            
            print(f"\nFound {len(items)} messages (newest first):")
            print("-" * 80)
            
            for item in items[:20]:  # Show first 20 for display
                try:
                    # Get message ID - try multiple fields
                    msg_id = (item.get('item_id') or 
                             item.get('id') or 
                             item.get('client_context') or
                             'Unknown')
                    
                    # Get text
                    text = item.get('text', '[no text]')
                    
                    # Get sender
                    user_id = item.get('user_id', 'Unknown')
                    sender = f"ID:{user_id}"
                    if str(user_id) == self.my_user_id:
                        sender = f"{self.my_username} (YOU)"
                    
                    # Get timestamp
                    timestamp = ""
                    if 'timestamp' in item:
                        try:
                            ts = int(item['timestamp']) / 1000000  # Convert microseconds
                            timestamp = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            timestamp = str(item['timestamp'])
                    
                    # Display
                    display_text = text[:80] + "..." if len(text) > 80 else text
                    
                    print(f"ID: {msg_id}")
                    print(f"From: {sender}")
                    print(f"Time: {timestamp}")
                    print(f"Text: {display_text}")
                    print("-" * 40)
                    
                except Exception as e:
                    print(f"Error displaying message: {e}")
                    continue
                
        except Exception as e:
            print(f"Failed to view messages: {e}")
    
    def search_messages_raw_api(self):
        """Search messages using raw API with PROPER pagination"""
        if not self.logged_in:
            print("Please login first")
            return
        
        if not self.selected_thread_id:
            print("Please select a thread first")
            return
        
        print(f"\n=== SEARCH MESSAGES ===")
        
        keywords_input = input("Enter keywords (comma-separated): ").strip()
        if not keywords_input:
            print("No keywords provided")
            return
        
        keywords = [k.strip().lower() for k in keywords_input.split(",") if k.strip()]
        
        try:
            amount = input("Max messages to search (default 1000): ").strip()
            amount = int(amount) if amount.isdigit() else 1000
            
            print(f"Searching for: {', '.join(keywords)}")
            
            # Use PROPER pagination
            if amount > 75:
                items = self.fetch_all_messages_paginated(amount)
            else:
                response = self.client.private_request(f"direct_v2/threads/{self.selected_thread_id}/", params={
                    "visual_message_return_type": "unseen",
                    "direction": "older",
                    "limit": str(amount)
                })
                
                if not response or 'thread' not in response:
                    print("No thread data received")
                    return
                
                items = response['thread'].get('items', [])
            
            if not items:
                print("No messages found")
                return
            
            matches = []
            print(f"Scanning {len(items)} messages...")
            
            for i, item in enumerate(items, 1):
                try:
                    if i % 200 == 0:
                        print(f"Scanned {i}/{len(items)}...")
                    
                    text = item.get('text', '')
                    if not text:
                        continue
                    
                    text_lower = text.lower()
                    if any(keyword in text_lower for keyword in keywords):
                        matches.append(item)
                        
                        # Get message details - try multiple ID fields
                        msg_id = (item.get('item_id') or 
                                 item.get('id') or 
                                 item.get('client_context') or
                                 'Unknown')
                        
                        user_id = item.get('user_id', 'Unknown')
                        
                        sender = f"ID:{user_id}"
                        if str(user_id) == self.my_user_id:
                            sender = f"{self.my_username} (YOU)"
                        
                        display_text = text[:100] + "..." if len(text) > 100 else text
                        
                        print(f"\n✓ MATCH #{len(matches)}")
                        print(f"  ID: {msg_id}")
                        print(f"  From: {sender}")
                        print(f"  Text: {display_text}")
                        
                except Exception as e:
                    print(f"Error processing message {i}: {e}")
                    continue
            
            print(f"\n=== SEARCH COMPLETE ===")
            print(f"Found {len(matches)} matches out of {len(items)} messages")
            
            # Store matches for potential deletion
            self.last_matches = matches
            self.last_keywords = keywords
            
        except Exception as e:
            print(f"Search failed: {e}")
    
    def delete_messages_raw_api(self):
        """UNSEND messages using proper Instagram API endpoint"""
        if not self.logged_in:
            print("Please login first")
            return
        
        if not self.selected_thread_id:
            print("Please select a thread first")
            return
        
        print(f"\n=== UNSEND MESSAGES ===")
        
        # Check if we have recent search results
        if not hasattr(self, 'last_matches') or not self.last_matches:
            print("No recent search results. Please search for messages first (option 5).")
            return
        
        matches = self.last_matches
        keywords = self.last_keywords
        
        print(f"Found {len(matches)} messages matching: {', '.join(keywords)}")
        
        # Show what will be deleted
        own_messages = []
        other_messages = []
        
        for msg in matches:
            user_id = msg.get('user_id', '')
            if str(user_id) == self.my_user_id:
                own_messages.append(msg)
            else:
                other_messages.append(msg)
        
        print(f"\nYour messages: {len(own_messages)}")
        print(f"Other messages: {len(other_messages)}")
        
        if len(own_messages) == 0:
            print("No messages from your account to unsend.")
            return
        
        # Show messages that will be deleted
        print(f"\nMessages that will be UNSENT:")
        for i, msg in enumerate(own_messages[:10], 1):  # Show first 10
            text = msg.get('text', '')
            text = text[:50] + "..." if len(text) > 50 else text
            
            # Get proper message ID
            msg_id = (msg.get('item_id') or 
                     msg.get('id') or 
                     msg.get('client_context') or
                     'Unknown')
            
            print(f"{i:2d}. {msg_id}: {text}")
        
        if len(own_messages) > 10:
            print(f"... and {len(own_messages) - 10} more")
        
        # Confirmation
        confirm = input(f"\nType 'YES' to UNSEND {len(own_messages)} of your messages: ").strip()
        if confirm != 'YES':
            print("Unsend cancelled")
            return
        
        # UNSEND messages using proper API endpoint
        print(f"\nUnsending {len(own_messages)} messages...")
        deleted = 0
        failed = 0
        
        for i, msg in enumerate(own_messages, 1):
            try:
                # Try multiple ID fields
                msg_id = (msg.get('item_id') or 
                         msg.get('id') or 
                         msg.get('client_context'))
                
                if not msg_id:
                    print(f"[{i}/{len(own_messages)}] SKIP: No message ID found")
                    failed += 1
                    continue
                
                print(f"[{i}/{len(own_messages)}] Unsending {msg_id}...", end=" ")
                
                # Use the UNSEND endpoint (not delete)
                response = self.client.private_request(
                    f"direct_v2/threads/{self.selected_thread_id}/items/{msg_id}/delete/",
                    data={
                        "_uuid": self.client.uuid,
                        "_uid": self.my_user_id,
                        "_csrftoken": self.client.token
                    },
                    with_signature=False
                )
                
                if response and response.get('status') == 'ok':
                    print("✓")
                    deleted += 1
                else:
                    # Try alternative unsend endpoint
                    response2 = self.client.private_request(
                        "direct_v2/threads/broadcast/item_unsend/",
                        data={
                            "thread_id": self.selected_thread_id,
                            "item_id": msg_id,
                            "_uuid": self.client.uuid,
                            "_uid": self.my_user_id,
                            "_csrftoken": self.client.token
                        },
                        with_signature=False
                    )
                    
                    if response2 and response2.get('status') == 'ok':
                        print("✓ (alt)")
                        deleted += 1
                    else:
                        print("✗")
                        failed += 1
                
                # Small delay between deletions
                time.sleep(1)
                
            except Exception as e:
                print(f"✗ Error: {e}")
                failed += 1
        
        print(f"\n=== UNSEND COMPLETE ===")
        print(f"Unsent: {deleted}")
        print(f"Failed: {failed}")
        
        # Clear search results
        self.last_matches = []
    
    def menu_loop(self):
        """Main menu"""
        while True:
            try:
                print("\n" + "=" * 50)
                print("INSTAGRAM DM TOOL - UNLIMITED PAGINATION")
                print("=" * 50)
                
                if self.logged_in:
                    print(f"Logged in as: {self.my_username}")
                else:
                    print("Not logged in")
                
                if self.selected_thread_id:
                    print(f"Selected thread: {self.selected_thread_id}")
                
                print("\nOptions:")
                print("1. Login")
                print("2. List Threads (Raw API)")
                print("3. Select Thread (by ID/username)")
                print("4. View Messages (Unlimited)")
                print("5. Search Messages (Unlimited)")
                print("6. Unsend Messages (Working)")
                print("7. Exit")
                
                choice = input("\nSelect option (1-7): ").strip()
                
                if choice == "1":
                    self.login()
                elif choice == "2":
                    self.list_threads_raw_api()
                elif choice == "3":
                    self.select_thread()
                elif choice == "4":
                    self.view_messages_raw_api()
                elif choice == "5":
                    self.search_messages_raw_api()
                elif choice == "6":
                    self.delete_messages_raw_api()
                elif choice == "7":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid option")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nMenu error: {e}")

def main():
    try:
        print("Instagram DM Tool - UNLIMITED PAGINATION + WORKING UNSEND")
        print("✓ Proper cursor-based pagination")
        print("✓ Can fetch 1000s of messages")
        print("✓ Working unsend functionality")
        tool = IGDMTool()
        tool.menu_loop()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
