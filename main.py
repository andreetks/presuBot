# config if script doesn't have access to the dns config
import dns.resolver
dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']

from typing import Final

# load telegram dependencies
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# libraries for spreadsheets manipulations
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account

import os
from dotenv import load_dotenv
load_dotenv()

TOKEN: Final = os.getenv('API_KEY')
BOT_USERNAME: Final = os.getenv('BOT_NAME')

# Lets us use the /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello there! I\'m a bot. What\'s up?')


# Lets us use the /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Try typing anything and I will do my best to respond!')


# Lets us use the /custom command
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is a custom command, you can add whatever text you want here.')

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
KEY = 'key.json'

SPREADSHEET_ID = os.getenv('SPREAD_ID')

creds = None
creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

def getRemaining():
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range='Presup!D16').execute()
    return result.get('values', [])[0][0]

def getExpenses():
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range='MarzAbril2024!C4:D32').execute()
    arrays = result.get('values', [])
    return arrays

def addExpense(pArray):
    nextCell = f'MarzAbril2024!C{len(getExpenses())+4}'
    print(nextCell)
    bodyCo = {
        "data": [ 
            { 
            "majorDimension": "ROWS", 
            "range": nextCell, 
            "values": [[pArray[0],pArray[1]]],
            },
        ],
        "valueInputOption": "USER_ENTERED",
    }
    sheet.values().batchUpdate(spreadsheetId=SPREADSHEET_ID,
                               body=bodyCo).execute()

    return 'success'

def getGasExpense():
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range='Presup!D11').execute()
    gasRemaining = result.get('values', [])
    return gasRemaining[0][0]

def addGasExpense(price):
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range='Presup!D11',valueRenderOption='FORMULA').execute()
    gasFormula = result.get('values', [])[0][0]

    bodyCo = {
        "data": [ 
            { 
            "majorDimension": "ROWS", 
            "range": 'Presup!D11', 
            "values": [[f'{gasFormula}-{price}']],
            },
        ],
        "valueInputOption": "USER_ENTERED",
    }
    sheet.values().batchUpdate(spreadsheetId=SPREADSHEET_ID,
                               body=bodyCo).execute()

    return getGasExpense()

def handle_response(text: str) -> str:
    # Create your own response logic
    processed: str = text.lower()

    if 'hello' in processed:
        return 'Hey there!'

    if 'send' in processed:
        arr = processed.split(' ')[1:]

        return addExpense(arr)
    
    if 'gastos' in processed:
        return getExpenses()
    
    if 'add gas' in processed:
        gasprice = processed.split(' ')[-1]
        return f'remaining gas -> {addGasExpense(gasprice)}'
    
    if 'getremaining' in processed:
        return getRemaining()
    
    if 'getgasremaining' in processed:
        return getGasExpense()

    return 'I don\'t understand'



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get basic info of the incoming message
    message_type: str = update.message.chat.type
    text: str = update.message.text

    # Print a log for debugging
    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    response: str = handle_response(text)

    # Reply normal if the message is in private
    print('Bot:', response)
    await update.message.reply_text(response)

    
# Log errors
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


# Run the program
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Log all errors
    app.add_error_handler(error)

    print('Polling...')
    # Run the bot
    app.run_polling(poll_interval=5)