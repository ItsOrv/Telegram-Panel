import asyncio
import logging
import os
import random
from typing import List, Tuple
import csv

from telethon import TelegramClient, functions, types
from telethon.errors import (
    AuthKeyUnregisteredError,
    FloodWaitError,
    RPCError,
    SessionPasswordNeededError,
    SessionRevokedError,
    UserDeactivatedError,
    UserNotMutualContactError,
    UserPrivacyRestrictedError,
)
from telethon.sessions import StringSession
from telethon.tl.functions.channels import (
    InviteToChannelRequest,
    JoinChannelRequest,
    LeaveChannelRequest,
    GetParticipantsRequest,
)
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.types import ChannelParticipantsSearch

logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

API_ID, API_HASH = (
    00,
    "",
)  # Get your API_ID and API_HASH from my.telegram.org
ACCOUNTS_FILE, COMMENTS_FILE = (
    "accounts.txt",
    "comments.txt",
)  # Path to accounts.txt and comments.txt
MIN_SLEEP, MAX_SLEEP = 3, 5  # Sleep time between sending requests (in seconds)


class TelegramManager:
    def __init__(self):
        self.accounts = self.load_file(ACCOUNTS_FILE)
        self.comments = self.load_file(COMMENTS_FILE)
        self.account_names = {}

    @staticmethod
    def load_file(filename: str) -> List[str]:
        if not os.path.exists(filename):
            open(filename, "w").close()
        with open(filename, "r") as f:
            return f.read().splitlines()

    def save_account(self, session_string: str):
        with open(ACCOUNTS_FILE, "a") as f:
            f.write(f"{session_string}\n")
        self.accounts.append(session_string)

    def remove_account(self, session_string: str):
        if session_string in self.accounts:
            self.accounts.remove(session_string)
            with open(ACCOUNTS_FILE, "w") as f:
                f.write("\n".join(self.accounts))
            logger.info("Account removed from accounts.txt.")
        else:
            logger.warning("Attempted to remove non-existent account.")

    async def sync_account_names(self):
        for session_string in self.accounts:
            client = None
            try:
                client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
                await client.connect()
                if not await client.is_user_authorized():
                    continue
                me = await client.get_me()
                self.account_names[session_string] = (
                    f"{me.first_name} {me.last_name or ''}"
                    if me.first_name
                    else me.phone
                )
            except Exception as e:
                logger.error(f"Error syncing account name: {e}")
            finally:
                if client and client.is_connected():
                    await client.disconnect()

    async def add_account(self, phone_number: str):
        try:
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            await client.send_code_request(phone_number)
            code = input("Enter the code you received: ")
            try:
                await client.sign_in(phone_number, code)
            except SessionPasswordNeededError:
                password = input(
                    "Two-factor authentication is enabled. Please enter your password: "
                )
                await client.sign_in(password=password)

            me = await client.get_me()
            session_string = client.session.save()
            self.save_account(session_string)
            self.account_names[session_string] = (
                f"{me.first_name} {me.last_name or ''}"
                if me.first_name
                else phone_number
            )

            await client.disconnect()
            logger.info(f"Account added: {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Error adding account {phone_number}: {e}")
            return False

    async def perform_action(self, action, *args):
        for session_str in self.accounts[:]:
            client = None
            try:
                client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
                await client.connect()
                if not await client.is_user_authorized():
                    raise SessionRevokedError("Session is no longer valid")
                await action(client, *args)
            except (
                UserDeactivatedError,
                SessionRevokedError,
                AuthKeyUnregisteredError,
            ):
                logger.warning("Account deleted or session revoked. Removing account.")
                self.remove_account(session_str)
            except FloodWaitError as e:
                logger.warning(f"Flood wait error: wait {e.seconds} seconds.")
            except RPCError as e:
                logger.error(f"RPC error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
            finally:
                if client and client.is_connected():
                    await client.disconnect()
            await asyncio.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))

    @staticmethod
    async def join_channel(client: TelegramClient, channel_name: str):
        await client(JoinChannelRequest(channel_name))
        logger.info(f"Joined channel {channel_name}")

    @staticmethod
    async def leave_channel(client: TelegramClient, channel_name: str):
        await client(LeaveChannelRequest(channel_name))
        logger.info(f"Left channel {channel_name}")

    @staticmethod
    async def send_reaction(
        client: TelegramClient, message_link: str, reaction_emoji: str
    ):
        channel, message_id = TelegramManager.parse_message_link(message_link)
        await client(
            functions.messages.SendReactionRequest(
                peer=channel,
                msg_id=message_id,
                reaction=[types.ReactionEmoji(emoticon=reaction_emoji)],
            )
        )
        logger.info(f"Sent {reaction_emoji} reaction to message in {channel}")

    async def send_random_comment(
        self, client: TelegramClient, channel: str, message_id: int
    ):
        comment = random.choice(self.comments)
        await client.send_message(channel, comment, comment_to=message_id)
        logger.info(f"Sent random comment to message {message_id} in {channel}")

    @staticmethod
    async def send_custom_comment(
        client: TelegramClient, channel: str, message_id: int, comment: str
    ):
        await client.send_message(channel, comment, comment_to=message_id)
        logger.info(f"Sent custom comment to message {message_id} in {channel}")

    @staticmethod
    def parse_message_link(link: str) -> Tuple[str, int]:
        parts = link.split("/")
        return parts[-2], int(parts[-1])


class TelegramManagerCLI:
    def __init__(self):
        self.manager = TelegramManager()

    @staticmethod
    def display_menu():
        print(
            r"""    
   / _ \_______________________/`/\+-/\'\'\
 \_\(_)/_/   orca-tg-manager   -+-    -+-+-
  _//o\\_                      \'\\/+-\/`/`/
   /   \                        \/-+--\/`/ 
 By PinkOrca
 Codeberg: https://codeberg.org/PinkOrca
 Telegram: @PinkOrca
 """
        )
        print("\nMenu:")
        print("1. Add accounts")
        print("2. Join channel")
        print("3. Leave channel")
        print("4. Send reaction")
        print("5. Send random comment")
        print("6. Send custom comment")
        print("7. List contacts from all accounts")
        print("8. Add all contacts to a group")
        print("9. Export members from a channel/group")
        print("10. Exit")

    async def add_accounts(self):
        while True:
            phone_number = input("Enter phone number (or 'done'): ").strip()
            if phone_number.lower() == "done":
                break
            await self.manager.add_account(phone_number)
            await asyncio.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))

    async def join_channel(self):
        channel_name = input("Enter channel username: ").strip()
        await self.manager.perform_action(self.manager.join_channel, channel_name)

    async def leave_channel(self):
        channel_name = input("Enter channel username: ").strip()
        await self.manager.perform_action(self.manager.leave_channel, channel_name)

    async def send_reaction(self):
        message_link = input("Enter message link: ").strip()
        reaction_emoji = input("Enter reaction emoji: ").strip()
        await self.manager.perform_action(
            self.manager.send_reaction, message_link, reaction_emoji
        )

    async def send_random_comment(self):
        post_link = input("Enter post link: ").strip()
        channel, message_id = self.manager.parse_message_link(post_link)
        await self.manager.perform_action(
            self.manager.send_random_comment, channel, message_id
        )

    async def send_custom_comment(self):
        post_link = input("Enter post link: ").strip()
        custom_comment = input("Enter your comment: ").strip()
        channel, message_id = self.manager.parse_message_link(post_link)
        await self.manager.perform_action(
            self.manager.send_custom_comment, channel, message_id, custom_comment
        )

    @staticmethod
    async def list_contacts(client: TelegramClient):
        try:
            contacts = await client(GetContactsRequest(hash=0))
            contact_count = len(contacts.users)

            for user in contacts.users:
                if user.phone:
                    print(
                        f"Name: {user.first_name} {user.last_name or ''}, Phone: {user.phone}"
                    )

            print(f"Total Contacts: {contact_count}")
            return contact_count
        except Exception as e:
            logger.error(f"Error retrieving contacts: {str(e)}")
            return 0

    async def list_all_contacts(self):
        total_contacts = 0
        for session_string in self.manager.accounts:
            client = None
            try:
                client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
                await client.connect()
                if not await client.is_user_authorized():
                    raise SessionRevokedError("Session is no longer valid")

                print(f"\nListing contacts for account: {session_string[:10]}...")
                account_contacts = await self.list_contacts(client)
                total_contacts += account_contacts
            except (
                UserDeactivatedError,
                SessionRevokedError,
                AuthKeyUnregisteredError,
            ):
                logger.warning("Account deleted or session revoked. Removing account.")
                self.manager.remove_account(session_string)
            except Exception as e:
                logger.error(
                    f"Failed to retrieve contacts for account {session_string[:10]}...: {str(e)}"
                )
            finally:
                if client and client.is_connected():
                    await client.disconnect()

        print(f"\nTotal number of contacts across all accounts: {total_contacts}")

    async def add_all_contacts_to_group(self):
        group_username = input("Enter the username of the public group: ").strip()
        total_added = 0

        for session_string in self.manager.accounts:
            client = None
            try:
                client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
                await client.connect()
                if not await client.is_user_authorized():
                    raise SessionRevokedError("Session is no longer valid")

                print(f"\nProcessing account: {session_string[:10]}...")

                try:
                    await client(JoinChannelRequest(group_username))
                    print("Successfully joined the public group/channel.")
                    entity = await client.get_entity(group_username)
                except ValueError as e:
                    print(f"Failed to join or get entity: {str(e)}")
                    continue
                except Exception as e:
                    print(f"An error occurred while joining: {str(e)}")
                    continue

                contacts = await client(GetContactsRequest(hash=0))

                for user in contacts.users:
                    try:
                        await client(InviteToChannelRequest(entity, [user]))
                        print(
                            f"Added {user.first_name} {user.last_name or ''} to the group"
                        )
                        total_added += 1
                        await asyncio.sleep(random.uniform(1, 3))
                    except UserPrivacyRestrictedError:
                        print(
                            f"Couldn't add {user.first_name} {user.last_name or ''} due to their privacy settings"
                        )
                    except UserNotMutualContactError:
                        print(
                            f"Couldn't add {user.first_name} {user.last_name or ''} as they're not a mutual contact"
                        )
                    except Exception as e:
                        print(
                            f"Error adding {user.first_name} {user.last_name or ''}: {str(e)}"
                        )

            except Exception as e:
                logger.error(
                    f"Failed to process account {session_string[:10]}...: {str(e)}"
                )
            finally:
                if client and client.is_connected():
                    await client.disconnect()

        print(f"\nTotal contacts added to the group: {total_added}")

    async def export_members(self):
        if not self.manager.accounts:
            print("No accounts available. Please add an account first.")
            return

        await self.manager.sync_account_names()

        print("Select an account:")
        for i, session_string in enumerate(self.manager.accounts):
            account_name = self.manager.account_names.get(
                session_string, f"Account {i+1}"
            )
            print(f"{i + 1}. {account_name}")

        account_index = int(input("Enter the number of the account: ")) - 1
        if account_index < 0 or account_index >= len(self.manager.accounts):
            print("Invalid account number.")
            return

        session_string = self.manager.accounts[account_index]
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)

        try:
            await client.connect()
            if not await client.is_user_authorized():
                raise SessionRevokedError("Session is no longer valid")

            channel_username = input("Enter the channel or group username: ").strip()
            entity = await client.get_entity(channel_username)

            if not entity.admin_rights:
                print("You are not an admin of this channel or group.")
                return

            all_participants = []
            offset = 0
            limit = 100

            while True:
                participants = await client(
                    GetParticipantsRequest(
                        entity, ChannelParticipantsSearch(""), offset, limit, hash=0
                    )
                )
                if not participants.users:
                    break
                all_participants.extend(participants.users)
                offset += len(participants.users)

            filename = (
                input("Enter the name for the CSV file (without .csv): ").strip()
                + ".csv"
            )
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "User ID", "Username"])
                for user in all_participants:
                    writer.writerow(
                        [
                            f"{user.first_name} {user.last_name or ''}",
                            user.id,
                            user.username or "",
                        ]
                    )

            print(f"Exported {len(all_participants)} members to {filename}")

        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            await client.disconnect()

    async def run(self):
        actions = {
            "1": self.add_accounts,
            "2": self.join_channel,
            "3": self.leave_channel,
            "4": self.send_reaction,
            "5": self.send_random_comment,
            "6": self.send_custom_comment,
            "7": self.list_all_contacts,
            "8": self.add_all_contacts_to_group,
            "9": self.export_members,
        }
        while True:
            self.display_menu()
            choice = input("Choose an option: ").strip()
            if choice == "10":
                break
            elif choice in actions:
                await actions[choice]()
            else:
                print("Invalid option. Try again.")


if __name__ == "__main__":
    cli = TelegramManagerCLI()
    asyncio.run(cli.run())
