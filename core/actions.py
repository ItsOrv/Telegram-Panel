from telethon import functions, types

async def join_channel(client, channel_name):
    try:
        await client(functions.channels.JoinChannelRequest(channel=channel_name))
        return True
    except Exception as e:
        print(f"Error joining channel: {e}")
        return False

async def leave_channel(client, channel_name):
    try:
        await client(functions.channels.LeaveChannelRequest(channel=channel_name))
        return True
    except Exception as e:
        print(f"Error leaving channel: {e}")
        return False

async def send_reaction(client, message_link, reaction_emoji):
    try:
        channel, message_id = parse_message_link(message_link)
        await client(functions.messages.SendReactionRequest(
            peer=channel,
            msg_id=message_id,
            reaction=[types.ReactionEmoji(emoticon=reaction_emoji)]
        ))
        return True
    except Exception as e:
        print(f"Error sending reaction: {e}")
        return False

async def send_comment(client, message_link, comment):
    try:
        channel, message_id = parse_message_link(message_link)
        await client.send_message(channel, comment, comment_to=message_id)
        return True
    except Exception as e:
        print(f"Error sending comment: {e}")
        return False

def parse_message_link(link):
    parts = link.split("/")
    return parts[-2], int(parts[-1])
