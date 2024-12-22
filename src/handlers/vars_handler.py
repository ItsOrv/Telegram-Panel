from telethon import events
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class VarsHandler:
    def __init__(self, bot):
        """
        Initialize VarsHandler with bot instance.

        :param bot: Instance of the bot to access configuration and manage conversations.
        """
        self.bot = bot

    async def add_keyword_handler(self, event):
        """Add a keyword to monitor."""
        logger.info("Executing add_keyword_handler in VarsHandler")
        try:
            # Check if user has triggered this function via a callback
            if isinstance(event, events.CallbackQuery.Event):
                await event.respond("Please enter the keyword you want to add.")
                self.bot._conversations[event.chat_id] = 'add_keyword_handler'
                return

            # Get and add keyword
            keyword = event.message.text.strip()
            if keyword not in self.bot.config['KEYWORDS']:
                self.bot.config['KEYWORDS'].append(keyword)
                self.bot.config_manager.save_config(self.bot.config)
                await event.respond(f"Keyword '{keyword}' added successfully")
            else:
                await event.respond(f"Keyword '{keyword}' already exists")

            # Respond with the list of current keywords
            keywords = ', '.join(self.bot.config['KEYWORDS'])
            await event.respond(f"📝 Current keywords: {keywords}")

        except Exception as e:
            logger.error(f"Error adding keyword: {e}")
            await event.respond("Error adding keyword. Please try again.")

    async def remove_keyword_handler(self, event):
        """Remove a keyword from monitoring."""
        logger.info("Executing remove_keyword_handler in VarsHandler")
        try:
            if isinstance(event, events.CallbackQuery.Event):
                await event.respond("Please enter the keyword you want to remove.")
                self.bot._conversations[event.chat_id] = 'remove_keyword_handler'
                return

            keyword = event.message.text.strip()
            if keyword in self.bot.config['KEYWORDS']:
                self.bot.config['KEYWORDS'].remove(keyword)
                self.bot.config_manager.save_config(self.bot.config)
                await event.respond(f"Keyword '{keyword}' removed successfully")
            else:
                await event.respond(f"Keyword '{keyword}' not found")

            keywords = ', '.join(self.bot.config['KEYWORDS'])
            await event.respond(f"📝 Current keywords: {keywords}")

        except Exception as e:
            logger.error(f"Error removing keyword: {e}")
            await event.respond("Error removing keyword. Please try again.")

    async def ignore_user_handler(self, event):
        """Ignore a user from further interaction."""
        logger.info("Executing ignore_user_handler in VarsHandler")
        try:
            if isinstance(event, events.CallbackQuery.Event):
                await event.respond("Please enter the user ID you want to ignore.")
                self.bot._conversations[event.chat_id] = 'ignore_user_handler'
                return

            user_id = int(event.message.text.strip())
            if user_id not in self.bot.config['IGNORE_USERS']:
                self.bot.config['IGNORE_USERS'].append(user_id)
                self.bot.config_manager.save_config(self.bot.config)
                await event.respond(f"User ID {user_id} is now ignored")
            else:
                await event.respond(f"User ID {user_id} is already ignored")

            ignored_users = ', '.join(map(str, self.bot.config['IGNORE_USERS']))
            await event.respond(f"📋 Ignored users: {ignored_users}")

        except ValueError:
            await event.respond("Invalid user ID format. Please enter a numeric user ID.")
        except Exception as e:
            logger.error(f"Error ignoring user: {e}")
            await event.respond("Error ignoring user. Please try again.")

    async def delete_ignore_user_handler(self, event):
        """Remove a user from the ignore list."""
        logger.info("Executing delete_ignore_user_handler in VarsHandler")
        try:
            if isinstance(event, events.CallbackQuery.Event):
                await event.respond("Please enter the user ID you want to stop ignoring.")
                self.bot._conversations[event.chat_id] = 'delete_ignore_user_handler'
                return

            user_id = int(event.message.text.strip())
            if user_id in self.bot.config['IGNORE_USERS']:
                self.bot.config['IGNORE_USERS'].remove(user_id)
                self.bot.config_manager.save_config(self.bot.config)
                await event.respond(f"User ID {user_id} is no longer ignored")
            else:
                await event.respond(f"User ID {user_id} not found in ignored list")

            ignored_users = ', '.join(map(str, self.bot.config['IGNORE_USERS']))
            await event.respond(f"📋 Ignored users: {ignored_users}")

        except ValueError:
            await event.respond("Invalid user ID format. Please enter a numeric user ID.")
        except Exception as e:
            logger.error(f"Error deleting ignored user: {e}")
            await event.respond("Error deleting ignored user. Please try again.")

    async def ignore_user(self, user_id, event):  # for channel button
        """Ignore a user from further interaction."""
        logger.info("Executing ignore_user in VarsHandler")
        try:
            if user_id not in self.bot.config['IGNORE_USERS']:
                self.bot.config['IGNORE_USERS'].append(user_id)
                self.bot.config_manager.save_config(self.bot.config)
                await event.respond(f"User ID {user_id} is now ignored")
            else:
                await event.respond(f"User ID {user_id} is already ignored")

        except Exception as e:
            logger.error(f"Error ignoring user: {e}")
            await event.respond("Error ignoring user. Please try again.")

    async def add_varshandler(self, event):
        """Add a variable to the handler."""
        logger.info("Executing add_varshandler in VarsHandler")
        try:
            if isinstance(event, events.CallbackQuery.Event):
                await event.respond("Please enter the variable you want to add.")
                self.bot._conversations[event.chat_id] = 'add_varshandler'
                return

            variable = event.message.text.strip()
            # Assuming there's a config list for variables
            if variable not in self.bot.config['VARIABLES']:
                self.bot.config['VARIABLES'].append(variable)
                self.bot.config_manager.save_config(self.bot.config)
                await event.respond(f"Variable '{variable}' added successfully")
            else:
                await event.respond(f"Variable '{variable}' already exists")

            variables = ', '.join(self.bot.config['VARIABLES'])
            await event.respond(f"📝 Current variables: {variables}")

        except Exception as e:
            logger.error(f"Error adding variable: {e}")
            await event.respond("Error adding variable. Please try again.")

    async def remove_varshandler(self, event):
        """Remove a variable from the handler."""
        logger.info("Executing remove_varshandler in VarsHandler")
        try:
            if isinstance(event, events.CallbackQuery.Event):
                await event.respond("Please enter the variable you want to remove.")
                self.bot._conversations[event.chat_id] = 'remove_varshandler'
                return

            variable = event.message.text.strip()
            if variable in self.bot.config['VARIABLES']:
                self.bot.config['VARIABLES'].remove(variable)
                self.bot.config_manager.save_config(self.bot.config)
                await event.respond(f"Variable '{variable}' removed successfully")
            else:
                await event.respond(f"Variable '{variable}' not found")

            variables = ', '.join(self.bot.config['VARIABLES'])
            await event.respond(f"📝 Current variables: {variables}")

        except Exception as e:
            logger.error(f"Error removing variable: {e}")
            await event.respond("Error removing variable. Please try again.")

