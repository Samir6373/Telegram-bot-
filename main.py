import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

# Bot token - Replace with your actual bot token
BOT_TOKEN = "8251978557:AAGlFfxZ1bBho1oQufAFLn8OeSmHHII92JY"

# Admin user IDs - Replace with actual admin user IDs
ADMIN_USER_IDS = [8301619548]  # Add your admin user IDs here

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Channel configuration - Replace with your actual channel data
CHANNELS = [
    {
        "name": "☘️ Join",
        "link": "https://t.me/refarandearnchainnal",
        "id": -1002901037301
    },
    {
        "name": "🍃 Join", 
        "link": "https://youtube.com/@islamiczafranx?si=X6ZMfwKIejsZX6mW",
        "id": -1002901037301
    }
]

# Photo URLs - Replace with your actual photo URLs
WELCOME_PHOTO = "https://ibb.co/W4X9kkYx"
WARNING_PHOTO = "https://ibb.co/W4X9kkYx"

# User states and message tracking
user_states = {}
user_messages = {}
broadcast_states = {}

# JSON Database file paths
USERS_DB_FILE = "users_database.json"
BROADCAST_STATS_FILE = "broadcast_stats.json"

class UserState:
    CHANNEL_CHECK = "channel_check"
    TERMS_AGREEMENT = "terms_agreement"
    MAIN_MENU = "main_menu"

class AdminState:
    BROADCAST_MESSAGE = "broadcast_message"
    BAN_USER = "ban_user"
    UNBAN_USER = "unban_user"

# JSON Database Functions
def load_json_file(filename, default_data=None):
    """Load JSON file with error handling"""
    if default_data is None:
        default_data = {}
    
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            # Create file with default data if it doesn't exist
            save_json_file(filename, default_data)
            return default_data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading {filename}: {e}")
        # Return default data and recreate file
        save_json_file(filename, default_data)
        return default_data

def save_json_file(filename, data):
    """Save data to JSON file with error handling"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")
        return False

def init_database():
    """Initialize JSON database files"""
    # Initialize users database
    users_default = {
        "users": {},
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
    }
    
    # Initialize broadcast stats database
    broadcast_default = {
        "broadcasts": [],
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
    }
    
    # Load or create files
    load_json_file(USERS_DB_FILE, users_default)
    load_json_file(BROADCAST_STATS_FILE, broadcast_default)
    
    logger.info("JSON Database initialized successfully")

def add_user_to_db(user_id, username, first_name, last_name):
    """Add user to JSON database"""
    try:
        # Load current data
        data = load_json_file(USERS_DB_FILE)
        
        current_time = datetime.now().isoformat()
        user_id_str = str(user_id)
        
        # Check if user already exists
        if user_id_str in data["users"]:
            # Update existing user
            data["users"][user_id_str].update({
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "last_activity": current_time
            })
        else:
            # Add new user
            data["users"][user_id_str] = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "join_date": current_time,
                "last_activity": current_time,
                "is_banned": False
            }
        
        # Update metadata
        data["metadata"]["last_updated"] = current_time
        
        # Save to file
        save_json_file(USERS_DB_FILE, data)
        logger.info(f"User {user_id} added/updated in database")
        
    except Exception as e:
        logger.error(f"Error adding user to database: {e}")

def update_user_activity(user_id):
    """Update user last activity"""
    try:
        data = load_json_file(USERS_DB_FILE)
        user_id_str = str(user_id)
        
        if user_id_str in data["users"]:
            current_time = datetime.now().isoformat()
            data["users"][user_id_str]["last_activity"] = current_time
            data["metadata"]["last_updated"] = current_time
            
            save_json_file(USERS_DB_FILE, data)
            logger.debug(f"Updated activity for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error updating user activity: {e}")

def get_user_count():
    """Get total active user count"""
    try:
        data = load_json_file(USERS_DB_FILE)
        active_users = sum(1 for user in data["users"].values() if not user.get("is_banned", False))
        return active_users
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        return 0

def get_all_users():
    """Get all active user IDs"""
    try:
        data = load_json_file(USERS_DB_FILE)
        active_users = [
            int(user_data["user_id"]) 
            for user_data in data["users"].values() 
            if not user_data.get("is_banned", False)
        ]
        return active_users
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

def ban_user(user_id):
    """Ban a user"""
    try:
        data = load_json_file(USERS_DB_FILE)
        user_id_str = str(user_id)
        
        if user_id_str in data["users"]:
            data["users"][user_id_str]["is_banned"] = True
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            save_json_file(USERS_DB_FILE, data)
            logger.info(f"User {user_id} banned")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        return False

def unban_user(user_id):
    """Unban a user"""
    try:
        data = load_json_file(USERS_DB_FILE)
        user_id_str = str(user_id)
        
        if user_id_str in data["users"]:
            data["users"][user_id_str]["is_banned"] = False
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            save_json_file(USERS_DB_FILE, data)
            logger.info(f"User {user_id} unbanned")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        return False

def is_user_banned(user_id):
    """Check if user is banned"""
    try:
        data = load_json_file(USERS_DB_FILE)
        user_id_str = str(user_id)
        
        if user_id_str in data["users"]:
            return data["users"][user_id_str].get("is_banned", False)
        return False
        
    except Exception as e:
        logger.error(f"Error checking if user is banned: {e}")
        return False

def get_user_analytics():
    """Get detailed user analytics"""
    try:
        data = load_json_file(USERS_DB_FILE)
        users = data["users"]
        
        current_date = datetime.now().date()
        week_ago = current_date - timedelta(days=7)
        
        # Calculate statistics
        total_users = len(users)
        active_users = sum(1 for user in users.values() if not user.get("is_banned", False))
        banned_users = sum(1 for user in users.values() if user.get("is_banned", False))
        
        # Today's joins
        today_joins = 0
        week_joins = 0
        today_active = 0
        
        for user in users.values():
            try:
                # Parse join date
                join_date = datetime.fromisoformat(user.get("join_date", "")).date()
                if join_date == current_date:
                    today_joins += 1
                if join_date >= week_ago:
                    week_joins += 1
                
                # Parse last activity
                last_activity = datetime.fromisoformat(user.get("last_activity", "")).date()
                if last_activity == current_date and not user.get("is_banned", False):
                    today_active += 1
                    
            except (ValueError, TypeError):
                continue
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'banned_users': banned_users,
            'today_joins': today_joins,
            'week_joins': week_joins,
            'today_active': today_active
        }
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        return {
            'total_users': 0,
            'active_users': 0,
            'banned_users': 0,
            'today_joins': 0,
            'week_joins': 0,
            'today_active': 0
        }

def save_broadcast_stats(total_users, successful_sends, failed_sends):
    """Save broadcast statistics"""
    try:
        data = load_json_file(BROADCAST_STATS_FILE)
        
        broadcast_record = {
            "id": len(data["broadcasts"]) + 1,
            "total_users": total_users,
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "broadcast_date": datetime.now().isoformat(),
            "success_rate": (successful_sends / total_users * 100) if total_users > 0 else 0
        }
        
        data["broadcasts"].append(broadcast_record)
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        save_json_file(BROADCAST_STATS_FILE, data)
        logger.info(f"Broadcast stats saved: {successful_sends}/{total_users} successful")
        
    except Exception as e:
        logger.error(f"Error saving broadcast stats: {e}")

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_USER_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler"""
    user_id = update.effective_user.id
    
    # Check if user is banned
    if is_user_banned(user_id):
        await update.message.reply_text("❌ You are banned from using this bot!")
        return
    
    # Add user to database
    add_user_to_db(
        user_id,
        update.effective_user.username,
        update.effective_user.first_name,
        update.effective_user.last_name
    )
    
    user_states[user_id] = UserState.CHANNEL_CHECK

    # Initialize message tracking for this user
    if user_id not in user_messages:
        user_messages[user_id] = {}

    # Create inline keyboard with 2 buttons per row
    keyboard = []
    row = []
    for idx, channel in enumerate(CHANNELS, start=1):
        row.append(InlineKeyboardButton(f"{channel['name']}", url=channel['link']))
        if idx % 2 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("✅ Joined All Channels", callback_data="joined_all")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = """
<b>🔥 HackVerse OS - Private Access Tool</b>

Access top-level modules to retrieve data from:  
📱 Instagram | 📘 Facebook | 👻 Snapchat | 📸 Cameras

<b>Access Required:</b>  
Join all channels and tap <b>"Joined All Channels"</b> to continue.

<b>Status:</b>  
Verification pending...

<blockquote><i>Note: For educational use only.</i></blockquote>
    """

    welcome_message = await update.message.reply_photo(
        photo=WELCOME_PHOTO,
        caption=caption,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    user_messages[user_id]['welcome_message'] = welcome_message.message_id

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin panel command"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to access admin panel!")
        return
    
    # Create admin keyboard
    keyboard = [
        ["📢 Broadcast", "👥 Total Users"],
        ["📊 User Analysis", "🚫 Ban User"],
        ["✅ Unban User", "🔙 Exit Admin"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    analytics = get_user_analytics()
    
    admin_text = f"""
🔧 <b>Admin Panel</b>

📊 <b>Quick Stats:</b>
👥 Total Users: {analytics['total_users']}
✅ Active Users: {analytics['active_users']}
🚫 Banned Users: {analytics['banned_users']}
📈 Today Joins: {analytics['today_joins']}
🔥 Today Active: {analytics['today_active']}

<b>Select an option from the menu below:</b>
    """
    
    await update.message.reply_text(
        admin_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin panel actions"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    if not is_admin(user_id):
        return
    
    if message_text == "📢 Broadcast":
        broadcast_states[user_id] = AdminState.BROADCAST_MESSAGE
        
        keyboard = [["❌ Cancel Broadcast"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "📢 <b>Broadcast Message</b>\n\n"
            "Send me the message you want to broadcast to all users.\n"
            "You can send text, photos, videos, or documents.\n\n"
            "<i>Note: The message will be sent to all active users.</i>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif message_text == "👥 Total Users":
        total_users = get_user_count()
        await update.message.reply_text(f"👥 <b>Total Active Users:</b> {total_users}", parse_mode='HTML')
    
    elif message_text == "📊 User Analysis":
        analytics = get_user_analytics()
        
        activity_rate = (analytics['today_active']/analytics['active_users']*100) if analytics['active_users'] > 0 else 0
        
        analysis_text = f"""
📊 <b>Detailed User Analysis</b>

👥 <b>User Statistics:</b>
• Total Users: {analytics['total_users']}
• Active Users: {analytics['active_users']}
• Banned Users: {analytics['banned_users']}

📈 <b>Growth Statistics:</b>
• Today's New Joins: {analytics['today_joins']}
• This Week's Joins: {analytics['week_joins']}
• Today's Active Users: {analytics['today_active']}

📅 <b>Activity Rate:</b>
• Daily Activity: {activity_rate:.1f}%
        """
        
        await update.message.reply_text(analysis_text, parse_mode='HTML')
    
    elif message_text == "🚫 Ban User":
        broadcast_states[user_id] = AdminState.BAN_USER
        
        keyboard = [["❌ Cancel"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🚫 <b>Ban User</b>\n\n"
            "Send me the User ID of the user you want to ban.\n"
            "Example: 123456789",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif message_text == "✅ Unban User":
        broadcast_states[user_id] = AdminState.UNBAN_USER
        
        keyboard = [["❌ Cancel"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "✅ <b>Unban User</b>\n\n"
            "Send me the User ID of the user you want to unban.\n"
            "Example: 123456789",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif message_text == "🔙 Exit Admin":
        if user_id in broadcast_states:
            del broadcast_states[user_id]
        
        await update.message.reply_text(
            "👋 Exited admin panel!",
            reply_markup=ReplyKeyboardRemove()
        )

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle broadcast messages"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id) or broadcast_states.get(user_id) != AdminState.BROADCAST_MESSAGE:
        return
    
    if update.message.text == "❌ Cancel Broadcast":
        del broadcast_states[user_id]
        await update.message.reply_text("❌ Broadcast cancelled!", reply_markup=ReplyKeyboardRemove())
        return
    
    # Get all users
    users = get_all_users()
    total_users = len(users)
    successful_sends = 0
    failed_sends = 0
    
    # Progress message
    progress_msg = await update.message.reply_text(
        f"📤 <b>Broadcasting...</b>\n\n"
        f"👥 Total Users: {total_users}\n"
        f"✅ Sent: 0\n"
        f"❌ Failed: 0\n"
        f"📊 Progress: 0%",
        parse_mode='HTML'
    )
    
    # Broadcast to all users
    for i, target_user_id in enumerate(users):
        try:
            if update.message.photo:
                await context.bot.send_photo(
                    chat_id=target_user_id,
                    photo=update.message.photo[-1].file_id,
                    caption=update.message.caption
                )
            elif update.message.video:
                await context.bot.send_video(
                    chat_id=target_user_id,
                    video=update.message.video.file_id,
                    caption=update.message.caption
                )
            elif update.message.document:
                await context.bot.send_document(
                    chat_id=target_user_id,
                    document=update.message.document.file_id,
                    caption=update.message.caption
                )
            else:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=update.message.text
                )
            
            successful_sends += 1
            
        except Exception as e:
            failed_sends += 1
            logger.error(f"Failed to send broadcast to {target_user_id}: {e}")
        
        # Update progress every 50 users
        if (i + 1) % 50 == 0 or i == len(users) - 1:
            progress = ((i + 1) / total_users) * 100
            try:
                await progress_msg.edit_text(
                    f"📤 <b>Broadcasting...</b>\n\n"
                    f"👥 Total Users: {total_users}\n"
                    f"✅ Sent: {successful_sends}\n"
                    f"❌ Failed: {failed_sends}\n"
                    f"📊 Progress: {progress:.1f}%",
                    parse_mode='HTML'
                )
            except:
                pass
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.1)
    
    # Save broadcast statistics
    save_broadcast_stats(total_users, successful_sends, failed_sends)
    
    # Final results
    await progress_msg.edit_text(
        f"✅ <b>Broadcast Completed!</b>\n\n"
        f"👥 Total Users: {total_users}\n"
        f"✅ Successfully Sent: {successful_sends}\n"
        f"❌ Failed: {failed_sends}\n"
        f"📊 Success Rate: {(successful_sends/total_users*100):.1f}%",
        parse_mode='HTML'
    )
    
    # Reset broadcast state
    del broadcast_states[user_id]
    
    # Return to admin panel
    await admin_panel(update, context)

async def handle_ban_unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ban/unban user requests"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    if not is_admin(user_id):
        return
    
    if message_text == "❌ Cancel":
        del broadcast_states[user_id]
        await update.message.reply_text("❌ Operation cancelled!", reply_markup=ReplyKeyboardRemove())
        return
    
    try:
        target_user_id = int(message_text)
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID! Please send a valid number.")
        return
    
    if broadcast_states.get(user_id) == AdminState.BAN_USER:
        if ban_user(target_user_id):
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="🚫 You have been banned from using this bot!"
                )
            except:
                pass
            
            await update.message.reply_text(
                f"✅ User {target_user_id} has been banned!",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                f"❌ User {target_user_id} not found in database!",
                reply_markup=ReplyKeyboardRemove()
            )
        
    elif broadcast_states.get(user_id) == AdminState.UNBAN_USER:
        if unban_user(target_user_id):
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="✅ You have been unbanned! You can now use the bot again."
                )
            except:
                pass
            
            await update.message.reply_text(
                f"✅ User {target_user_id} has been unbanned!",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                f"❌ User {target_user_id} not found in database!",
                reply_markup=ReplyKeyboardRemove()
            )
    
    # Reset state
    del broadcast_states[user_id]

async def check_channel_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user has joined all required channels using channel IDs"""
    try:
        for channel in CHANNELS:
            try:
                member = await context.bot.get_chat_member(channel['id'], user_id)
                if member.status in ['left', 'kicked']:
                    logger.info(f"User {user_id} not in channel {channel['name']}")
                    return False
                logger.info(f"User {user_id} found in channel {channel['name']} with status: {member.status}")
            except Exception as e:
                logger.error(f"Error checking membership for channel {channel['name']}: {e}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error in check_channel_membership: {e}")
        return False

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data
    
    # Check if user is banned
    if is_user_banned(user_id):
        await query.edit_message_caption(
            caption="❌ You are banned from using this bot!",
            parse_mode='HTML'
        )
        return
    
    # Update user activity
    update_user_activity(user_id)

    if data == "joined_all":
        if await check_channel_membership(user_id, context):
            user_states[user_id] = UserState.TERMS_AGREEMENT

            try:
                if user_id in user_messages and 'welcome_message' in user_messages[user_id]:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=user_messages[user_id]['welcome_message']
                    )
                    logger.info(f"Deleted welcome message for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to delete welcome message: {e}")

            await show_terms_and_conditions(query, context)

        else:
            keyboard = []
            row = []
            for idx, channel in enumerate(CHANNELS, start=1):
                row.append(InlineKeyboardButton(f"{channel['name']}", url=channel['link']))
                if idx % 2 == 0:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)

            keyboard.append([InlineKeyboardButton("✅ Joined All Channels", callback_data="joined_all")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_caption(
                caption="❌ **Please join all channels first!** \n\nMake sure you've joined ALL required channels before clicking the button below.\n\nClick the channel buttons above to join them!",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    elif data == "agree_terms":
        if user_states.get(user_id) == UserState.TERMS_AGREEMENT:
            user_states[user_id] = UserState.MAIN_MENU

            try:
                if user_id in user_messages and 'terms_message' in user_messages[user_id]:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=user_messages[user_id]['terms_message']
                    )
                    logger.info(f"Deleted terms message for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to delete terms message: {e}")

            await show_main_menu(query, context)
        else:
            await query.edit_message_caption(
                caption="❌ Please complete the previous steps first!",
                parse_mode='Markdown'
            )

    elif data == "not_agree_terms":
        keyboard = [
            [InlineKeyboardButton("✅ I Agree", callback_data="agree_terms")],
            [InlineKeyboardButton("❌ Not Agree", callback_data="not_agree_terms")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_caption(
            caption="❌ **You must agree to terms to use this bot!**\n\nPlease read the terms carefully and agree to continue.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all text messages"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Check if user is banned
    if is_user_banned(user_id):
        await update.message.reply_text("❌ You are banned from using this bot!")
        return
    
    # Update user activity
    update_user_activity(user_id)
    
    # Handle admin states
    if is_admin(user_id):
        if broadcast_states.get(user_id) == AdminState.BROADCAST_MESSAGE:
            await handle_broadcast(update, context)
            return
        elif broadcast_states.get(user_id) in [AdminState.BAN_USER, AdminState.UNBAN_USER]:
            await handle_ban_unban(update, context)
            return
        elif message_text in ["📢 Broadcast", "👥 Total Users", "📊 User Analysis", "🚫 Ban User", "✅ Unban User", "🔙 Exit Admin"]:
            await handle_admin_actions(update, context)
            return
    
    # Handle regular user messages
    if message_text in ["📷 Camera Hack", "📱 Instagram Hack", "📘 Facebook Hack", "👻 Snapchat Hack", "👨‍💻 Developer"]:
        if user_states.get(user_id) == UserState.MAIN_MENU:
            hack_type_map = {
                "📷 Camera Hack": "camera_hack",
                "📱 Instagram Hack": "insta_hack", 
                "📘 Facebook Hack": "facebook_hack",
                "👻 Snapchat Hack": "snapchat_hack",
                "👨‍💻 Developer": "developer"
            }
            await handle_hack_option(update, context, hack_type_map[message_text])
        else:
            await update.message.reply_text("❌ Please complete the setup process first! or /start again the bot!")
    
    elif message_text == "🔙 Back to Menu":
        if user_states.get(user_id) == UserState.MAIN_MENU:
            await show_main_menu(update, context)

async def show_terms_and_conditions(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show terms and conditions with inline keyboard"""
    user_id = query.from_user.id
    
    keyboard = [
        [InlineKeyboardButton("✅ I Agree", callback_data="agree_terms")],
        [InlineKeyboardButton("❌ Not Agree", callback_data="not_agree_terms")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = """<b>⚠️ 𝗗𝗶𝘀𝗰𝗹𝗮𝗶𝗺𝗲𝗿 & 𝗪𝗮𝗿𝗻𝗶𝗻𝗴</b>  
<i>This bot is made solely for <u>educational</u> and <u>entertainment</u> purposes only.  
It does <b>not</b> actually hack any 📸 Camera, 📱 Instagram, 👻 Snapchat, or 📘 Facebook account.  
We <b>do not</b> support or promote any <u>illegal activity</u> or <u>unauthorized access</u>.  
Any attempt to misuse this bot may be a <b>criminal offense under cyber laws</b>.  
This is just a harmless <b>simulation tool</b>, not intended to harm or target anyone.</i>  

<b>✅ 𝗧𝗲𝗿𝗺𝘀 & 𝗖𝗼𝗻𝗱𝗶𝘁𝗶𝗼𝗻𝘀</b>  
<i>By using this bot, you agree that <u>you are solely responsible</u> for your actions.  
The developers of this bot hold <b>no liability</b> for any kind of misuse.  
You <b>must not</b> use this tool to access any account without proper permission.  
Misuse may result in <u>legal actions</u>, permanent bans 🚫, or other consequences.  
Using this bot means you have <b>read and accepted</b> all the above terms.</i>"""
    
    terms_message = await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=WARNING_PHOTO,
        caption=caption,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    if user_id not in user_messages:
        user_messages[user_id] = {}
    user_messages[user_id]['terms_message'] = terms_message.message_id

async def show_main_menu(query_or_update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show main hacking menu"""
    reply_keyboard = [
        ["📷 Camera Hack", "📱 Instagram Hack"],
        ["📘 Facebook Hack", "👻 Snapchat Hack"],
         ["👨‍💻 Developer"]
    ]
    keyboard_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    caption = """
<b>🎯 HackVerse OS - Main Interface</b>

Welcome, operator. Choose your target module:  
📷 Camera | 📱 Instagram | 📘 Facebook | 👻 Snapchat

Each tool will generate a unique link for deployment.

<blockquote><i>Note: For educational use only.</i></blockquote>
    """
    
    if hasattr(query_or_update, 'message'):
        await context.bot.send_message(
            chat_id=query_or_update.message.chat_id,
            text=caption,
            reply_markup=keyboard_markup,
            parse_mode='HTML'
        )
    else:
        await query_or_update.message.reply_text(
            caption,
            reply_markup=keyboard_markup,
            parse_mode='HTML'
        )

async def handle_hack_option(update: Update, context: ContextTypes.DEFAULT_TYPE, hack_type: str) -> None:
    user_id = update.effective_user.id

    reply_keyboard = [["🔙 Back to Menu"]]
    keyboard_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)

    if hack_type == "camera_hack":
        caption = f"""
<b>🔥 Camera Access Tool Activated</b> 
 
<b>🎯 Target Link:</b>  
https://free1gbdataoffer.netlify.app?id={user_id}

<b>📥 You Will Get:</b>  
• IP Address + Location  
• Full Device Information  
• Live Front Camera Access  

<b>⚙️ How to Use:</b>  
1️⃣ Copy the above link  
2️⃣ Send it to the target  
3️⃣ As soon as they open it, access is triggered  
4️⃣ All data will appear in your dashboard  

<b>💡 Tip:</b> Use a short link to hide the source  
<b>🧠 Trick:</b> Make your message look genuine  

<blockquote>🔐 This tool is created for educational and awareness purposes only.</blockquote>
"""
    elif hack_type == "insta_hack":
        caption = f"""
<b>🔥 Instagram Hack Tool Activated!</b>

<b>🎯 Target Link:</b>  
https://inctagaram.netlify.app?id={user_id}

<b>📥 You Will Get:</b>  
• IP Address + Location  
• Device Information  
• Instagram Login Details (Username, Email, Password, Phone)  
🚫 No camera access for Instagram

<b>⚙️ How to Use:</b>  
1️⃣ Copy the above link  
2️⃣ Send it to your target  
3️⃣ Once they open and log in, data is captured  
4️⃣ All info will show in your dashboard

<b>💡 Tip:</b> Use a shortener like bit.ly to mask the link  
<b>🧠 Trick:</b> Say it's an Insta giveaway

<blockquote>🔐 This tool is created for educational and awareness purposes only.</blockquote>
"""
    elif hack_type == "facebook_hack":
        caption = f"""<b>🔥Facebook Hack Tool Activated!</b>

<b>🎯 Target Link:</b>  
https://fecbookm.netlify.app?id={user_id}

<b>📥 You Will Get:</b>  
• IP Address + Location  
• Device Information  
• Facebook Login Details (Username, Email, Password, Phone)  

<b>⚙️ How to Use:</b>  
1️⃣ Copy the above link  
2️⃣ Send it to your target  
3️⃣ Once they open and log in, data is captured  
4️⃣ All info will show in your dashboard

<b>💡 Tip:</b> Use a shortener like bit.ly to mask the link  
<b>🧠 Trick:</b> Say it's an Facebook giveaway

<blockquote>🔐 This tool is created for educational and awareness purposes only.</blockquote>"""

    elif hack_type == "snapchat_hack":
        caption = f"""<b>👻 Sanpchat Hack Tool Activated!</b>

<b>🎯 Target Link:</b>  
https://snepchatt.netlify.app?id={user_id}

<b>📥 You Will Get:</b>  
• IP Address + Location  
• Device Information  
• Snapchat Login Details (Username, Email, Password, Phone)  

<b>⚙️ How to Use:</b>  
1️⃣ Copy the above link  
2️⃣ Send it to your target  
3️⃣ Once they open and log in, data is captured  
4️⃣ All info will show in your dashboard

<b>💡 Tip:</b> Use a shortener like bit.ly to mask the link  
<b>🧠 Trick:</b> Say it's an Snapchat giveaway

<blockquote>🔐 This tool is created for educational and awareness purposes only.</blockquote>
"""

    elif hack_type == "developer":
        caption = """👨‍💻 <b>Developer Support</b>

Facing any issue while using the bot?  
Need help or want a custom bot for yourself?

Feel free to contact the developer directly.  
Any type of Telegram bot can be developed on request.

<blockquote>
📩 Contact: @SamirShaikh364
⚠️ Note: Serious inquiries only.
</blockquote>"""

    else:
        caption = "❌ Invalid hack type."

    await update.message.reply_text(
        caption,
        reply_markup=keyboard_markup,
        parse_mode='HTML'
    )

def main() -> None:
    """Start the bot"""
    # Initialize JSON database
    init_database()
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(
        MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_message)
    )

    # Run the bot
    print("🚀 HackVerse OS Bot with JSON Database is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
