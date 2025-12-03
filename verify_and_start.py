#!/usr/bin/env python3
"""Script to verify bot code and start it safely"""
import os
import sys
import subprocess
import time

def check_syntax():
    """Check Python syntax of all source files"""
    print("🔍 Checking syntax of source files...")
    source_files = [
        'src/actions.py',
        'src/Client.py',
        'src/Config.py',
        'src/Handlers.py',
        'src/Keyboards.py',
        'src/Logger.py',
        'src/Monitor.py',
        'src/Telbot.py',
        'src/Validation.py',
        'start_bot.py'
    ]
    
    errors = []
    for file in source_files:
        if os.path.exists(file):
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'py_compile', file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    errors.append(f"❌ {file}: {result.stderr}")
                    print(f"❌ Syntax error in {file}")
                else:
                    print(f"✅ {file} - OK")
            except Exception as e:
                errors.append(f"❌ {file}: {str(e)}")
                print(f"❌ Error checking {file}: {e}")
    
    if errors:
        print("\n❌ Syntax errors found:")
        for error in errors:
            print(f"  {error}")
        return False
    
    print("✅ All syntax checks passed!")
    return True

def check_imports():
    """Check if all imports work correctly"""
    print("\n🔍 Checking imports...")
    try:
        # Set environment variables
        os.environ['API_ID'] = '20019286'
        os.environ['API_HASH'] = '95b61445e99a09288982e9d891b44c3d'
        os.environ['BOT_TOKEN'] = '8324526593:AAGursSWD_-IuusFIdralGm4LsRRNoVQyHY'
        os.environ['ADMIN_ID'] = '7718839318'
        os.environ['CHANNEL_ID'] = ''
        os.environ['REPORT_CHECK_BOT'] = ''
        
        # Try importing main modules
        print("  Importing src.Config...")
        from src.Config import API_ID, API_HASH, BOT_TOKEN
        
        print("  Importing src.Telbot...")
        from src.Telbot import TelegramBot
        
        print("  Importing src.Handlers...")
        from src.Handlers import CommandHandler, CallbackHandler
        
        print("  Importing src.actions...")
        from src.actions import Actions
        
        print("✅ All imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def stop_existing_bot():
    """Stop any existing bot processes"""
    print("\n🛑 Stopping existing bot processes...")
    try:
        # Kill processes
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe', '/FI', 'WINDOWTITLE eq *start_bot*'],
                         capture_output=True, check=False, timeout=5)
        else:
            # Unix-like
            result = subprocess.run(['pkill', '-f', 'python.*start_bot'],
                                  capture_output=True, check=False, timeout=5)
            if result.returncode == 0:
                print("  ✅ Stopped existing bot processes")
            else:
                print("  ℹ️  No existing bot processes found")
        
        time.sleep(2)
        return True
    except Exception as e:
        print(f"  ⚠️  Could not stop processes: {e}")
        return True  # Continue anyway

def start_bot():
    """Start the bot"""
    print("\n🚀 Starting bot...")
    try:
        # Start bot in background
        process = subprocess.Popen(
            [sys.executable, 'start_bot.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        # Wait a bit and check if it's still running
        time.sleep(5)
        
        if process.poll() is None:
            print("  ✅ Bot process started successfully")
            print(f"  📝 Process PID: {process.pid}")
            return True, process
        else:
            stdout, stderr = process.communicate()
            print(f"  ❌ Bot process exited immediately!")
            print(f"  STDOUT: {stdout.decode()[:500]}")
            print(f"  STDERR: {stderr.decode()[:500]}")
            return False, None
    except Exception as e:
        print(f"  ❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def verify_bot_running():
    """Verify bot is actually running"""
    print("\n🔍 Verifying bot is running...")
    time.sleep(3)
    
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'],
                                  capture_output=True, text=True, check=False, timeout=5)
            if 'start_bot' in result.stdout:
                print("  ✅ Bot process found in task list")
                return True
        else:
            result = subprocess.run(['pgrep', '-f', 'python.*start_bot'],
                                  capture_output=True, text=True, check=False, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                print("  ✅ Bot process found (PID: {})".format(result.stdout.strip()))
                return True
        
        print("  ⚠️  Bot process not found in process list")
        return False
    except Exception as e:
        print(f"  ⚠️  Could not verify: {e}")
        return True  # Assume it's running if we can't check

def main():
    """Main verification and startup process"""
    print("=" * 60)
    print("🤖 Telegram Bot Verification and Startup")
    print("=" * 60)
    
    # Step 1: Check syntax
    if not check_syntax():
        print("\n❌ Syntax check failed! Fix errors before starting bot.")
        sys.exit(1)
    
    # Step 2: Check imports
    if not check_imports():
        print("\n❌ Import check failed! Fix errors before starting bot.")
        sys.exit(1)
    
    # Step 3: Stop existing bot
    stop_existing_bot()
    
    # Step 4: Start bot
    success, process = start_bot()
    
    if not success:
        print("\n❌ Failed to start bot!")
        sys.exit(1)
    
    # Step 5: Verify bot is running
    if verify_bot_running():
        print("\n" + "=" * 60)
        print("✅ Bot started successfully!")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("  1. Check bot_running.log for detailed logs")
        print("  2. Send /start to your bot in Telegram")
        print("  3. Verify bot responds correctly")
        print("\n💡 To stop the bot, run: pkill -f 'python.*start_bot'")
        return 0
    else:
        print("\n⚠️  Bot may not be running. Check bot_running.log for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

