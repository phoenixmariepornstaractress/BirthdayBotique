# https://github.com/eternnoir/pyTelegramBotAPI
#https://github.com/dbader/schedule

# BirthdayBotique

import telebot
import schedule
import time
from datetime import datetime
import random
import pyodbc
import logging

# Constants
API_TOKEN = 'YOUR_API_TOKEN_HERE'
ADMIN_CHAT_ID = 'YOUR_ADMIN_CHAT_ID_HERE'

# Initialize the bot
bot = telebot.TeleBot(API_TOKEN)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database connection function
def get_db_connection():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=your_server_name;'
            'DATABASE=your_database_name;'
            'UID=your_username;'
            'PWD=your_password'
        )
        return conn
    except pyodbc.Error as e:
        logging.error(f"Database connection failed: {e}")
        return None

# Helper Functions
def calculate_age(birthdate):
    """Calculate age based on the date of birth."""
    birthdate = datetime.strptime(birthdate, "%Y-%m-%d")
    today = datetime.now()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

def get_birthday_fact():
    """Return a random birthday fact."""
    facts = [
        "Your birthday falls on the same day as National Ice Cream Day!",
        "Did you know? You were born during the peak of the meteor shower!",
        "Your birthstone is the rare and beautiful sapphire!",
    ]
    return random.choice(facts)

def get_zodiac_sign(dob):
    """Calculate the zodiac sign based on the date of birth."""
    zodiacs = {
        (1, 20): "Aquarius", (2, 19): "Pisces", (3, 21): "Aries", (4, 20): "Taurus",
        (5, 21): "Gemini", (6, 21): "Cancer", (7, 23): "Leo", (8, 23): "Virgo",
        (9, 23): "Libra", (10, 23): "Scorpio", (11, 22): "Sagittarius", (12, 22): "Capricorn"
    }
    for (month, day), sign in zodiacs.items():
        if (dob.month == month and dob.day >= day) or (dob.month == month % 12 + 1 and dob.day < day):
            return sign
    return "Capricorn"

def get_gift_suggestion(zodiac_sign, hobbies=None):
    """Suggest a gift based on the zodiac sign or hobbies."""
    suggestions = {
        "Aries": "Consider a fitness tracker or something that supports their active lifestyle.",
        "Taurus": "A luxurious scented candle or gourmet chocolate would be perfect.",
        "Gemini": "Books or puzzles to stimulate their curious mind.",
        "Cancer": "A cozy blanket or a photo frame for their cherished memories.",
        # Add suggestions for other zodiac signs
    }
    return suggestions.get(zodiac_sign, "A thoughtful gift based on their hobbies would be great!")

def log_activity(chat_id, action):
    """Log user activities for future reference."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Logs (ChatID, Action) VALUES (?, ?)", (chat_id, action))
            conn.commit()
        except pyodbc.Error as e:
            logging.error(f"Failed to log activity: {e}")
        finally:
            cursor.close()
            conn.close()

def log_birthday_message(chat_id, message):
    """Log birthday messages sent by the bot."""
    log_activity(chat_id, f"Birthday Message: {message}")

def register_user(chat_id, dob):
    """Register or update user information in the database."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                IF EXISTS (SELECT 1 FROM Users WHERE ChatID = ?)
                BEGIN
                    UPDATE Users SET DOB = ?, UpdatedAt = GETDATE() WHERE ChatID = ?
                END
                ELSE
                BEGIN
                    INSERT INTO Users (ChatID, DOB) VALUES (?, ?)
                END
            """, (chat_id, dob, chat_id, chat_id, dob))
            conn.commit()
        except pyodbc.Error as e:
            logging.error(f"Failed to register/update user: {e}")
        finally:
            cursor.close()
            conn.close()

# Bot Command Handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Greet users when they start the bot."""
    chat_id = message.chat.id
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DOB FROM Users WHERE ChatID = ?", (chat_id,))
            user = cursor.fetchone()
            if user:
                bot.send_message(chat_id, "You're already registered! We'll send you a birthday wish on your special day!")
            else:
                bot.send_message(chat_id, "Welcome to the Birthday Bot! Please enter your date of birth in the format MM-DD-YYYY.")
        except pyodbc.Error as e:
            logging.error(f"Failed to send welcome message: {e}")
        finally:
            cursor.close()
            conn.close()

@bot.message_handler(func=lambda message: message.text and message.text.count('-') == 2)
def handle_dob(message):
    """Handle text messages to receive the date of birth."""
    chat_id = message.chat.id
    try:
        dob = datetime.strptime(message.text, "%m-%d-%Y")
        register_user(chat_id, dob)
        bot.send_message(chat_id, f"Thank you! We've recorded your date of birth as {dob.strftime('%B %d, %Y')}.")
        log_activity(chat_id, "DOB Registered")
    except ValueError:
        bot.send_message(chat_id, "The date format is incorrect. Please enter your date of birth in the format MM-DD-YYYY.")

@bot.message_handler(commands=['update_dob'])
def update_dob(message):
    """Update the date of birth."""
    chat_id = message.chat.id
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DOB FROM Users WHERE ChatID = ?", (chat_id,))
            user = cursor.fetchone()
            if user:
                bot.send_message(chat_id, "Please enter your new date of birth in the format MM-DD-YYYY.")
            else:
                bot.send_message(chat_id, "You haven't registered your date of birth yet. Use /start to register.")
        except pyodbc.Error as e:
            logging.error(f"Failed to update DOB: {e}")
        finally:
            cursor.close()
            conn.close()

@bot.message_handler(commands=['delete_dob'])
def delete_dob(message):
    """Delete the registered date of birth."""
    chat_id = message.chat.id
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Users WHERE ChatID = ?", (chat_id,))
            conn.commit()
            bot.send_message(chat_id, "Your date of birth has been deleted.")
        except pyodbc.Error as e:
            logging.error(f"Failed to delete DOB: {e}")
        finally:
            cursor.close()
            conn.close()

@bot.message_handler(commands=['view_dob'])
def view_dob(message):
    """View the registered date of birth."""
    chat_id = message.chat.id
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DOB FROM Users WHERE ChatID = ?", (chat_id,))
            user = cursor.fetchone()
            if user:
                dob = user[0].strftime("%B %d, %Y")
                bot.send_message(chat_id, f"Your registered date of birth is {dob}.")
            else:
                bot.send_message(chat_id, "You haven't registered your date of birth yet. Use /start to register.")
        except pyodbc.Error as e:
            logging.error(f"Failed to view DOB: {e}")
        finally:
            cursor.close()
            conn.close()

@bot.message_handler(commands=['list_birthdays'])
def list_birthdays(message):
    """Admin function to list all registered birthdays."""
    chat_id = message.chat.id
    if str(chat_id) == ADMIN_CHAT_ID:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT ChatID, DOB FROM Users")
                users = cursor.fetchall()
                if users:
                    all_birthdays = "Registered Birthdays:\n"
                    for user in users:
                        dob = user[1].strftime("%B %d, %Y")
                        all_birthdays += f"User ID {user[0]}: {dob}\n"
                    bot.send_message(chat_id, all_birthdays)
                else:
                    bot.send_message(chat_id, "No birthdays registered yet.")
            except pyodbc.Error as e:
                logging.error(f"Failed to list birthdays: {e}")
            finally:
                cursor.close()
                conn.close()
    else:
        bot.send_message(chat_id, "You don't have permission to use this command.")

@bot.message_handler(commands=['set_message'])
def set_custom_message(message):
    """Set a custom birthday message."""
    chat_id = message.chat.id
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DOB FROM Users WHERE ChatID = ?", (chat_id,))
            user = cursor.fetchone()
            if user:
                bot.send_message(chat_id, "Please enter your custom birthday message.")
                cursor.execute("UPDATE Users SET CustomMessage = ? WHERE ChatID = ?", (None, chat_id))
                conn.commit()
            else:
                bot.send_message(chat_id, "You haven't registered your date of birth yet. Use /start to register.")
        except pyodbc.Error as e:
            logging.error(f"Failed to set custom message: {e}")
        finally:
            cursor.close()
            conn.close()

@bot.message_handler(func=lambda message: True)
def handle_custom_message(message):
    """Handle custom birthday message input."""
    chat_id = message.chat.id
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT CustomMessage FROM Users WHERE ChatID = ?", (chat_id,))
            user = cursor.fetchone()
            if user and user[0] is None:
                cursor.execute("UPDATE Users SET CustomMessage = ? WHERE ChatID = ?", (message.text, chat_id))
                conn.commit()
                bot.send_message(chat_id, "Your custom birthday message has been set!")
                log_activity(chat_id, "Custom Message Set")
            else:
                bot.send_message(chat_id, "Please register your date of birth first using /start.")
        except pyodbc.Error as e:
            logging.error(f"Failed to handle custom message: {e}")
        finally:
            cursor.close()
            conn.close()

# Scheduler Functions
def send_birthday_message():
    """Send a birthday message to users whose birthdays are today."""
    today = datetime.now().strftime("%m-%d")
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ChatID, DOB, CustomMessage FROM Users WHERE FORMAT(DOB, 'MM-dd') = ?", (today,))
            users = cursor.fetchall()

            for user in users:
                chat_id, dob, custom_message = user
                age = calculate_age(dob.strftime("%Y-%m-%d"))
                zodiac_sign = get_zodiac_sign(dob)
                gift_suggestion = get_gift_suggestion(zodiac_sign)
                birthday_fact = get_birthday_fact()
                
                message = f"🎉 Happy Birthday! You are now {age} years old.\n" \
                          f"Zodiac Sign: {zodiac_sign}\n" \
                          f"Gift Suggestion: {gift_suggestion}\n" \
                          f"Fun Fact: {birthday_fact}"
                
                if custom_message:
                    message = custom_message
                
                bot.send_message(chat_id, message)
                log_birthday_message(chat_id, message)
        except pyodbc.Error as e:
            logging.error(f"Failed to send birthday message: {e}")
        finally:
            cursor.close()
            conn.close()

# Schedule the birthday message function
schedule.every().day.at("09:00").do(send_birthday_message)

# Run the bot and the scheduler
if __name__ == "__main__":
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            time.sleep(10)  # Sleep before restarting polling in case of an error
