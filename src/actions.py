import logging
import random
import asyncio
from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import SendVoteRequest, SendReactionRequest
from telethon.tl.types import ReactionEmoji, ReactionCustomEmoji
from src.Config import CHANNEL_ID
from src.Validation import InputValidator

logger = logging.getLogger(__name__)

# Concurrency limit for bulk operations to avoid rate limiting
MAX_CONCURRENT_OPERATIONS = 3

class Actions:
    def __init__(self, tbot):
        self.tbot = tbot
        self.operation_semaphore = asyncio.Semaphore(MAX_CONCURRENT_OPERATIONS)

    async def prompt_group_action(self, event, action_name):
        """
        Prompt the user to enter the number of accounts to be used for the group action.
        """
        async with self.tbot.active_clients_lock:
            total_accounts = len(self.tbot.active_clients)
        
        message = f"There are {total_accounts} accounts available. Please choose how many accounts (from 1 to {total_accounts}) will perform the {action_name} action."
        buttons = [Button.inline(str(i), f"{action_name}_{i}") for i in range(1, total_accounts + 1)]
        await event.respond(message, buttons=buttons)

    async def prompt_individual_action(self, event, action_name):
        """
        Show a list of account names as clickable buttons and prompt the user to select which account should perform the action.
        """
        async with self.tbot.active_clients_lock:
            sessions = list(self.tbot.active_clients.keys())
        
        buttons = [Button.inline(session, f"{action_name}_{session}") for session in sessions]
        await event.respond("Please select an account to perform the action:", buttons=buttons)

    async def handle_group_action(self, event, action_name, num_accounts):
        """
        Handle the group action by calling the respective bulk handler.
        For bulk operations, we need to get input once and apply to all accounts.
        """
        # Store number of accounts for bulk operations
        async with self.tbot._conversations_lock:
            self.tbot.handlers[f'bulk_{action_name}_count'] = num_accounts
        
        # Call the appropriate bulk handler
        bulk_handler_name = f'bulk_{action_name}_prompt'
        if hasattr(self, bulk_handler_name):
            await getattr(self, bulk_handler_name)(event)
        else:
            # Fallback to individual action flow (for backward compatibility)
            await getattr(self, action_name)(None, event)

    async def handle_individual_action(self, event, action_name, session):
        """
        Handle the individual action by calling the respective function for the selected account.
        """
        async with self.tbot.active_clients_lock:
            account = self.tbot.active_clients.get(session)
        
        if account:
            await getattr(self, action_name)(account, event)
        else:
            await event.respond(f"Account {session} not found.")

    async def reaction(self, account, event):
        """
        Perform the reaction action for individual account.
        """
        # Step 1: Ask for the link to the message
        await event.respond("Please provide the link to the message where the reaction will be applied.")
        async with self.tbot._conversations_lock:
            self.tbot._conversations[event.chat_id] = 'reaction_link_handler'
        if account:
            self.tbot.handlers['reaction_account'] = account

    async def bulk_reaction_prompt(self, event):
        """
        Prompt for bulk reaction - ask for link once.
        """
        await event.respond("Please provide the link to the message where reactions will be applied.")
        async with self.tbot._conversations_lock:
            self.tbot._conversations[event.chat_id] = 'bulk_reaction_link_handler'

    async def reaction_link_handler(self, event):
        """
        Handle the link input for individual reaction action.
        """
        try:
            link = event.message.text.strip()
            
            # Validate link
            is_valid, error_msg = InputValidator.validate_telegram_link(link)
            if not is_valid:
                await event.respond(f"❌ {error_msg}\nPlease try again.")
                return
            
            await event.respond("Please select a reaction:", buttons=[
                Button.inline("👍", b'reaction_thumbsup'),
                Button.inline("❤️", b'reaction_heart'),
                Button.inline("😂", b'reaction_laugh'),
                Button.inline("😮", b'reaction_wow'),
                Button.inline("😢", b'reaction_sad'),
                Button.inline("😡", b'reaction_angry')
            ])
            async with self.tbot._conversations_lock:
                self.tbot._conversations[event.chat_id] = 'reaction_select_handler'
            self.tbot.handlers['reaction_link'] = link
        except Exception as e:
            logger.error(f"Error in reaction_link_handler: {e}")
            await event.respond("Error processing link. Please try again.")
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            self.tbot.handlers.pop('reaction_link', None)

    async def bulk_reaction_link_handler(self, event):
        """
        Handle the link input for bulk reaction action.
        """
        try:
            link = event.message.text.strip()
            
            # Validate link
            is_valid, error_msg = InputValidator.validate_telegram_link(link)
            if not is_valid:
                await event.respond(f"❌ {error_msg}\nPlease try again.")
                return
            
            await event.respond("Please select a reaction:", buttons=[
                Button.inline("👍", b'bulk_reaction_thumbsup'),
                Button.inline("❤️", b'bulk_reaction_heart'),
                Button.inline("😂", b'bulk_reaction_laugh'),
                Button.inline("😮", b'bulk_reaction_wow'),
                Button.inline("😢", b'bulk_reaction_sad'),
                Button.inline("😡", b'bulk_reaction_angry')
            ])
            async with self.tbot._conversations_lock:
                self.tbot._conversations[event.chat_id] = 'bulk_reaction_select_handler'
            self.tbot.handlers['bulk_reaction_link'] = link
        except Exception as e:
            logger.error(f"Error in bulk_reaction_link_handler: {e}")
            await event.respond("Error processing link. Please try again.")
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            self.tbot.handlers.pop('bulk_reaction_link', None)

    async def reaction_select_handler(self, event):
        """
        Handle the reaction selection for individual account.
        """
        reaction_map = {
            'reaction_thumbsup': '👍',
            'reaction_heart': '❤️',
            'reaction_laugh': '😂',
            'reaction_wow': '😮',
            'reaction_sad': '😢',
            'reaction_angry': '😡'
        }
        
        data = event.data.decode() if hasattr(event, 'data') else event.message.text.strip()
        reaction = reaction_map.get(data, data)
        
        account = self.tbot.handlers.get('reaction_account')
        link = self.tbot.handlers.get('reaction_link')
        
        if account and link:
            # Apply reaction immediately for individual account
            try:
                await self.apply_reaction(account, link, reaction)
                await event.respond(f"Successfully applied {reaction} reaction using account {account.session.filename}")
            except Exception as e:
                logger.error(f"Error applying reaction: {e}")
                await event.respond(f"Error applying reaction: {str(e)}")
            finally:
                # Cleanup
                async with self.tbot._conversations_lock:
                    self.tbot._conversations.pop(event.chat_id, None)
                self.tbot.handlers.pop('reaction_link', None)
                self.tbot.handlers.pop('reaction_account', None)
        else:
            await event.respond("Error: Missing account or link information.")

    async def bulk_reaction_select_handler(self, event):
        """
        Handle the reaction selection for bulk operation.
        Applies reaction to all selected accounts immediately.
        """
        reaction_map = {
            'bulk_reaction_thumbsup': '👍',
            'bulk_reaction_heart': '❤️',
            'bulk_reaction_laugh': '😂',
            'bulk_reaction_wow': '😮',
            'bulk_reaction_sad': '😢',
            'bulk_reaction_angry': '😡'
        }
        
        data = event.data.decode() if hasattr(event, 'data') else event.message.text.strip()
        reaction = reaction_map.get(data, data)
        
        link = self.tbot.handlers.get('bulk_reaction_link')
        num_accounts = self.tbot.handlers.get('bulk_reaction_count')
        
        if link and num_accounts:
            # Get accounts
            async with self.tbot.active_clients_lock:
                accounts = list(self.tbot.active_clients.values())[:num_accounts]
            
            # Apply reactions with concurrency control
            async def apply_reaction_with_limit(account):
                async with self.operation_semaphore:
                    try:
                        await self.apply_reaction(account, link, reaction)
                        await asyncio.sleep(random.uniform(2, 5))
                    except Exception as e:
                        logger.error(f"Error applying reaction with account {account.session.filename}: {e}")
            
            # Execute all reactions
            tasks = [apply_reaction_with_limit(account) for account in accounts]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            await event.respond(f"Applied {reaction} reaction using {num_accounts} accounts.")
            
            # Cleanup
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            self.tbot.handlers.pop('bulk_reaction_link', None)
            self.tbot.handlers.pop('bulk_reaction_count', None)
        else:
            await event.respond("Error: Missing link or account count information.")


    def parse_telegram_link(self, link):
        """
        Parse Telegram link to extract chat_id and message_id.
        Returns: (chat_id, message_id) tuple
        """
        try:
            parts = link.split('/')
            if 't.me/c/' in link:
                # Format: https://t.me/c/1234567890/123
                chat_id = int('-100' + parts[-2])
                message_id = int(parts[-1])
                return chat_id, message_id
            else:
                # Format: https://t.me/username/123
                chat_username = parts[-2].replace('@', '')
                message_id = int(parts[-1])
                return chat_username, message_id
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing link {link}: {e}")
            raise ValueError(f"Invalid Telegram link format: {link}")

    async def apply_reaction(self, account, link, reaction):
        """
        Apply the selected reaction using the given account.
        Uses SendReactionRequest to properly react to messages.
        """
        try:
            # Parse link to get chat_id and message_id
            chat_id, message_id = self.parse_telegram_link(link)
            
            # Map emoji to reaction
            reaction_map = {
                '👍': ReactionEmoji(emoticon='👍'),
                '❤️': ReactionEmoji(emoticon='❤️'),
                '😂': ReactionEmoji(emoticon='😂'),
                '😮': ReactionEmoji(emoticon='😮'),
                '😢': ReactionEmoji(emoticon='😢'),
                '😡': ReactionEmoji(emoticon='😡')
            }
            
            # Get reaction object
            reaction_obj = reaction_map.get(reaction, ReactionEmoji(emoticon=reaction))
            
            # Get entity if it's a username
            if isinstance(chat_id, str):
                entity = await account.get_entity(chat_id)
                chat_id = entity.id
            
            # Send reaction using SendReactionRequest
            await account(SendReactionRequest(
                peer=chat_id,
                msg_id=message_id,
                reaction=[reaction_obj]
            ))
            logger.info(f"Applied {reaction} reaction using account {account.session.filename}")
        except Exception as e:
            logger.error(f"Error applying reaction: {e}", exc_info=True)
            raise

    async def poll(self, account, event):
        """
        Perform the poll action - vote on a poll.
        """
        await event.respond("Please provide the link to the poll:")
        async with self.tbot._conversations_lock:
            self.tbot._conversations[event.chat_id] = 'poll_link_handler'
        self.tbot.handlers['poll_account'] = account

    async def poll_link_handler(self, event):
        """
        Handle the poll link input.
        """
        try:
            link = event.message.text.strip()
            
            # Validate link
            is_valid, error_msg = InputValidator.validate_telegram_link(link)
            if not is_valid:
                await event.respond(f"❌ {error_msg}\nPlease try again.")
                return
            
            self.tbot.handlers['poll_link'] = link
            await event.respond("Please enter the option number you want to vote for (e.g., 1, 2, 3):")
            async with self.tbot._conversations_lock:
                self.tbot._conversations[event.chat_id] = 'poll_option_handler'
        except Exception as e:
            logger.error(f"Error in poll_link_handler: {e}")
            await event.respond("Error processing link. Please try again.")
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            self.tbot.handlers.pop('poll_account', None)
            self.tbot.handlers.pop('poll_link', None)

    async def poll_option_handler(self, event):
        """
        Handle the poll option selection.
        """
        try:
            # Validate poll option
            is_valid, error_msg, option_num = InputValidator.validate_poll_option(event.message.text.strip())
            if not is_valid:
                await event.respond(f"❌ {error_msg}\nPlease try again.")
                return
            
            option = option_num - 1  # Convert to 0-based index
            account = self.tbot.handlers.get('poll_account')
            link = self.tbot.handlers.get('poll_link')
            
            # Parse the link to get chat and message IDs
            parts = link.split('/')
            if 't.me/c/' in link:
                chat_id = int('-100' + parts[-2])
                message_id = int(parts[-1])
            else:
                chat_username = parts[-2]
                message_id = int(parts[-1])
                chat_id = chat_username
            
            # Get the poll message
            message = await account.get_messages(chat_id, ids=message_id)
            if message.poll:
                await account(SendVoteRequest(
                    peer=chat_id,
                    msg_id=message_id,
                    options=[bytes([option])]
                ))
                await event.respond(f"Successfully voted option {option + 1} using account {account.session.filename}")
            else:
                await event.respond("The provided link does not point to a poll.")
            
            # Cleanup
            self.tbot.handlers.pop('poll_account', None)
            self.tbot.handlers.pop('poll_link', None)
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            
        except Exception as e:
            logger.error(f"Error voting on poll: {e}")
            await event.respond(f"Error voting on poll: {str(e)}")
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)

    async def join(self, account, event):
        """
        Perform the join action - join a group or channel.
        """
        await event.respond("Please provide the group/channel link or username to join:")
        async with self.tbot._conversations_lock:
            self.tbot._conversations[event.chat_id] = 'join_link_handler'
        self.tbot.handlers['join_account'] = account

    async def join_link_handler(self, event):
        """
        Handle the join link input.
        """
        try:
            link = event.message.text.strip()
            
            # Validate link
            is_valid, error_msg = InputValidator.validate_telegram_link(link)
            if not is_valid:
                await event.respond(f"❌ {error_msg}")
                return
            
            account = self.tbot.handlers.get('join_account')
            
            # Join the group/channel
            await account.join_chat(link)
            await event.respond(f"Successfully joined {link} using account {account.session.filename}")
            
            # Cleanup
            self.tbot.handlers.pop('join_account', None)
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            
        except Exception as e:
            logger.error(f"Error joining group/channel: {e}")
            await event.respond(f"Error joining group/channel: {str(e)}")
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)

    async def left(self, account, event):
        """
        Perform the left action - leave a group or channel.
        """
        await event.respond("Please provide the group/channel link or username to leave:")
        async with self.tbot._conversations_lock:
            self.tbot._conversations[event.chat_id] = 'left_link_handler'
        self.tbot.handlers['left_account'] = account

    async def left_link_handler(self, event):
        """
        Handle the leave link input.
        """
        try:
            link = event.message.text.strip()
            
            # Validate link
            is_valid, error_msg = InputValidator.validate_telegram_link(link)
            if not is_valid:
                await event.respond(f"❌ {error_msg}")
                return
            
            account = self.tbot.handlers.get('left_account')
            
            # Leave the group/channel
            entity = await account.get_entity(link)
            await account.leave_chat(entity)
            await event.respond(f"Successfully left {link} using account {account.session.filename}")
            
            # Cleanup
            self.tbot.handlers.pop('left_account', None)
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            
        except Exception as e:
            logger.error(f"Error leaving group/channel: {e}")
            await event.respond(f"Error leaving group/channel: {str(e)}")
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)

    async def block(self, account, event):
        """
        Perform the block action - block a user.
        """
        await event.respond("Please provide the user ID or username to block:")
        async with self.tbot._conversations_lock:
            self.tbot._conversations[event.chat_id] = 'block_user_handler'
        self.tbot.handlers['block_account'] = account

    async def block_user_handler(self, event):
        """
        Handle the block user input.
        """
        try:
            user_input = event.message.text.strip()
            account = self.tbot.handlers.get('block_account')
            
            # Block the user
            from telethon.tl.functions.contacts import BlockRequest
            entity = await account.get_entity(user_input)
            await account(BlockRequest(entity))
            await event.respond(f"Successfully blocked user {user_input} using account {account.session.filename}")
            
            # Cleanup
            self.tbot.handlers.pop('block_account', None)
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            
        except Exception as e:
            logger.error(f"Error blocking user: {e}")
            await event.respond(f"Error blocking user: {str(e)}")
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)

    async def send_pv(self, account, event):
        """
        Perform the send_pv action - send a private message to a user.
        """
        await event.respond("Please provide the user ID or username to send a message to:")
        async with self.tbot._conversations_lock:
            self.tbot._conversations[event.chat_id] = 'send_pv_user_handler'
        self.tbot.handlers['send_pv_account'] = account

    async def send_pv_user_handler(self, event):
        """
        Handle the send_pv user input.
        """
        try:
            user_input = event.message.text.strip()
            self.tbot.handlers['send_pv_user'] = user_input
            await event.respond("Please enter the message you want to send:")
            async with self.tbot._conversations_lock:
                self.tbot._conversations[event.chat_id] = 'send_pv_message_handler'
        except Exception as e:
            logger.error(f"Error in send_pv_user_handler: {e}")
            await event.respond("Error processing user input. Please try again.")
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            self.tbot.handlers.pop('send_pv_account', None)
            self.tbot.handlers.pop('send_pv_user', None)

    async def send_pv_message_handler(self, event):
        """
        Handle the send_pv message input.
        """
        try:
            message = event.message.text.strip()
            
            # Validate message text
            is_valid, error_msg = InputValidator.validate_message_text(message)
            if not is_valid:
                await event.respond(f"❌ {error_msg}\nPlease try again.")
                return
            
            account = self.tbot.handlers.get('send_pv_account')
            user_input = self.tbot.handlers.get('send_pv_user')
            
            # Send the private message
            entity = await account.get_entity(user_input)
            await account.send_message(entity, message)
            await event.respond(f"Successfully sent message to {user_input} using account {account.session.filename}")
            
            # Cleanup
            self.tbot.handlers.pop('send_pv_account', None)
            self.tbot.handlers.pop('send_pv_user', None)
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            
        except Exception as e:
            logger.error(f"Error sending private message: {e}")
            await event.respond(f"Error sending private message: {str(e)}")
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)

    async def comment(self, account, event):
        """
        Perform the comment action - comment on a post/message.
        """
        await event.respond("Please provide the link to the post/message:")
        async with self.tbot._conversations_lock:
            self.tbot._conversations[event.chat_id] = 'comment_link_handler'
        self.tbot.handlers['comment_account'] = account

    async def comment_link_handler(self, event):
        """
        Handle the comment link input.
        """
        try:
            link = event.message.text.strip()
            
            # Validate link
            is_valid, error_msg = InputValidator.validate_telegram_link(link)
            if not is_valid:
                await event.respond(f"❌ {error_msg}\nPlease try again.")
                return
            
            self.tbot.handlers['comment_link'] = link
            await event.respond("Please enter your comment:")
            async with self.tbot._conversations_lock:
                self.tbot._conversations[event.chat_id] = 'comment_text_handler'
        except Exception as e:
            logger.error(f"Error in comment_link_handler: {e}")
            await event.respond("Error processing link. Please try again.")
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            self.tbot.handlers.pop('comment_account', None)
            self.tbot.handlers.pop('comment_link', None)

    async def comment_text_handler(self, event):
        """
        Handle the comment text input.
        """
        try:
            comment_text = event.message.text.strip()
            
            # Validate comment text
            is_valid, error_msg = InputValidator.validate_message_text(comment_text)
            if not is_valid:
                await event.respond(f"❌ {error_msg}\nPlease try again.")
                return
            
            account = self.tbot.handlers.get('comment_account')
            link = self.tbot.handlers.get('comment_link')
            
            # Parse the link to get chat and message IDs
            parts = link.split('/')
            if 't.me/c/' in link:
                chat_id = int('-100' + parts[-2])
                message_id = int(parts[-1])
            else:
                chat_username = parts[-2]
                message_id = int(parts[-1])
                chat_id = chat_username
            
            # Send the comment
            await account.send_message(chat_id, comment_text, reply_to=message_id)
            await event.respond(f"Successfully posted comment using account {account.session.filename}")
            
            # Cleanup
            self.tbot.handlers.pop('comment_account', None)
            self.tbot.handlers.pop('comment_link', None)
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)
            
        except Exception as e:
            logger.error(f"Error posting comment: {e}")
            await event.respond(f"Error posting comment: {str(e)}")
            async with self.tbot._conversations_lock:
                self.tbot._conversations.pop(event.chat_id, None)

