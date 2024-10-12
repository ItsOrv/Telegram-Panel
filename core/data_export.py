import csv
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch

async def export_members(client, channel_username, filename):
    try:
        channel = await client.get_entity(channel_username)
        all_participants = []
        offset = 0
        limit = 100

        while True:
            participants = await client(GetParticipantsRequest(
                channel, ChannelParticipantsSearch(''), offset, limit,
                hash=0
            ))
            if not participants.users:
                break
            all_participants.extend(participants.users)
            offset += len(participants.users)

        with open(filename, "w", encoding="UTF-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Username", "User ID", "First Name", "Last Name"])
            for user in all_participants:
                writer.writerow([user.username, user.id, user.first_name, user.last_name])

        return True
    except Exception as e:
        print(f"Error exporting members: {e}")
        return False
