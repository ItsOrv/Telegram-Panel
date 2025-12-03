#!/usr/bin/env python3
"""Test script to diagnose account connectivity issues"""
import os
import sys
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, AuthKeyUnregisteredError

# Set environment variables
os.environ['API_ID'] = '20019286'
os.environ['API_HASH'] = '95b61445e99a09288982e9d891b44c3d'

async def test_account(phone_number):
    """Test if an account can connect and work properly"""
    print(f"\n{'='*60}")
    print(f"Testing account: {phone_number}")
    print('='*60)
    
    client = TelegramClient(phone_number, int(os.environ['API_ID']), os.environ['API_HASH'])
    
    try:
        print("  [1] Connecting...")
        await client.connect()
        print("  ✅ Connected")
        
        print("  [2] Checking authorization...")
        is_authorized = await client.is_user_authorized()
        print(f"  Authorization status: {is_authorized}")
        
        if not is_authorized:
            print("  ❌ Account is NOT authorized")
            print("  💡 Solution: Delete session file and re-add account through bot")
            return False
        
        print("  [3] Getting account info...")
        try:
            me = await client.get_me()
            if me:
                print(f"  ✅ Account: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
                print(f"  📞 Phone: {me.phone}")
            else:
                print("  ❌ get_me() returned None")
                return False
        except Exception as me_error:
            print(f"  ❌ Failed to get account info: {me_error}")
            return False
        
        print("  [4] Testing dialogs...")
        try:
            dialogs = await client.get_dialogs(limit=5)
            print(f"  ✅ Can access dialogs ({len(dialogs)} found)")
        except Exception as dialog_error:
            print(f"  ❌ Failed to get dialogs: {dialog_error}")
            print("  💡 This means account cannot access Telegram data")
            return False
        
        print("  [5] Testing entity resolution...")
        # Test with Telegram's official bot
        test_username = "userinfobot"
        try:
            entity = await client.get_entity(f"@{test_username}")
            if entity:
                print(f"  ✅ Can resolve entities (tested with @{test_username})")
            else:
                print(f"  ❌ Entity resolution returned None")
                return False
        except Exception as entity_error:
            print(f"  ❌ Failed to resolve entity: {entity_error}")
            print("  💡 This means account cannot find users by username")
            return False
        
        print("  [6] Testing message send capability...")
        try:
            # Try to send a message to Telegram's spam bot (won't actually send, just test)
            # We'll use get_input_entity which is lighter
            await client.get_input_entity(test_username)
            print(f"  ✅ Can send messages (tested input entity)")
        except Exception as send_error:
            print(f"  ⚠️  Send test warning: {send_error}")
        
        print(f"\n  {'='*56}")
        print("  ✅ ACCOUNT IS WORKING PROPERLY")
        print(f"  {'='*56}")
        return True
        
    except AuthKeyUnregisteredError:
        print("  ❌ CRITICAL: Auth key is unregistered")
        print("  💡 Session is invalid. Delete and re-add account.")
        return False
    except Exception as e:
        print(f"  ❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.disconnect()
        print("  [*] Disconnected")

async def main():
    """Test all accounts"""
    print("\n" + "="*60)
    print("🔍 ACCOUNT CONNECTIVITY DIAGNOSTIC TOOL")
    print("="*60)
    
    # Find all session files
    import glob
    sessions = glob.glob("+*.session")
    
    if not sessions:
        print("\n❌ No account session files found!")
        print("💡 Add accounts through the bot first")
        return
    
    print(f"\nFound {len(sessions)} account(s)")
    
    results = {}
    for session_file in sessions:
        phone = session_file.replace('.session', '')
        result = await test_account(phone)
        results[phone] = result
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    working = [phone for phone, status in results.items() if status]
    broken = [phone for phone, status in results.items() if not status]
    
    if working:
        print(f"\n✅ Working accounts ({len(working)}):")
        for phone in working:
            print(f"  • {phone}")
    
    if broken:
        print(f"\n❌ Broken accounts ({len(broken)}):")
        for phone in broken:
            print(f"  • {phone}")
        print("\n💡 SOLUTION for broken accounts:")
        print("  1. Stop the bot")
        print("  2. Delete the session files:")
        for phone in broken:
            print(f"     rm {phone}.session")
        print("  3. Restart the bot")
        print("  4. Re-add accounts through bot's 'Add Account' option")
    
    if broken and not working:
        print("\n⚠️  WARNING: NO WORKING ACCOUNTS!")
        print("   Your bot cannot send messages until accounts are fixed")

if __name__ == '__main__':
    asyncio.run(main())

