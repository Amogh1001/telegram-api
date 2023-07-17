import tweepy
from typing import Final
import requests
import json
from googleapiclient.discovery import build
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from tokens import TOKEN, BOT_USERNAME, api_key, consumer_key, consumer_secret, access_token, access_token_secret

TOKEN: Final = TOKEN
BOT_USERNAME: Final = BOT_USERNAME
api_key = api_key
consumer_key = consumer_key
consumer_secret = consumer_secret
access_token = access_token
access_token_secret = access_token_secret

video_id = ""

params = {
    'q': 'ryzen',
    'key': api_key
}

def video_comments(video_id, api_key):
    # List for storing comments and replies
    comments_and_replies = []

    # Creating YouTube resource object
    youtube = build('youtube', 'v3', developerKey=api_key)

    try:
        # Retrieve YouTube video comments
        video_response = youtube.commentThreads().list(
            part='snippet,replies',
            videoId=video_id,
            maxResults=100,  # Increase if needed
            textFormat='plainText'
        ).execute()

        # Iterate through video comments
        while video_response:
            for item in video_response['items']:
                # Extract comment
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']

                # Count number of replies to the comment
                reply_count = item['snippet']['totalReplyCount']

                if reply_count > 0:
                    # Iterate through all replies
                    for reply in item['replies']['comments']:
                        # Extract reply
                        reply_text = reply['snippet']['textDisplay']
                        # Append comment and reply as a tuple
                        comments_and_replies.append((comment, reply_text))

                else:
                    # Append comment and an empty reply as a tuple
                    comments_and_replies.append((comment, ''))

            # Check if there are more pages of results
            if 'nextPageToken' in video_response:
                video_response = youtube.commentThreads().list(
                    part='snippet,replies',
                    videoId=video_id,
                    maxResults=100,
                    textFormat='plainText',
                    pageToken=video_response['nextPageToken']
                ).execute()
            else:
                break

    except Exception as e:
        print('An error occurred:', str(e))

    return comments_and_replies

print('Starting up bot...')

# Lets us use the /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello there! I\'m a bot. What\'s up?\n/help: for help')


# Lets us use the /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('/start: starts the bot')
    await update.message.reply_text('/help: displays commands')
    await update.message.reply_text('/echo <type here>: echos the message and displays the video')
    await update.message.reply_text('/search <type here>: searches in youtube and displays the results')
    await update.message.reply_text('/tweet <type here>: tweets the message')

#Lets us use the /echo command
async def echo_callback(update, context):
    user_says = " ".join(context.args)
    video_id = user_says
    await update.message.reply_text("You said: " + video_id)
    await update.message.reply_text("https://www.youtube.com/watch?v="+video_id)
    comments = video_comments(video_id, api_key)
    for comment, reply in comments:
        await update.message.reply_text('Comment: '+ comment)
        await update.message.reply_text('Reply: '+ reply+"\n")

async def search(update, context):
    user_says = " ".join(context.args)
    params['q'] = user_says
    r = requests.get('https://www.googleapis.com/youtube/v3/search?', params=params, headers={'Accept': 'application/json'})
    links=[]
    data = r.json()
    if 'items' in data:
        for item in data['items']:
            if(item['id']['kind'] != 'youtube#video'):
                # print(item['id']['channelId'])
                links.append("https://www.youtube.com/channel/"+item['id']['channelId'])
            else:
                # print(item['id']['videoId'])
                links.append("https://www.youtube.com/watch?v="+item['id']['videoId'])
    for link in links:
        await update.message.reply_text(link)

async def tweet(update, context):
    user_says = " ".join(context.args)
    twitter_client = tweepy.Client(
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        access_token=access_token, access_token_secret=access_token_secret
    )
    response = twitter_client.create_tweet(
        text=user_says
    )
    await update.message.reply_text("Tweeted: "+user_says)


def handle_response(text: str) -> str:
    # Create your own response logic
    processed: str = text.lower()

    if 'hello' in processed:
        return 'Hey there!'

    if 'how are you' in processed:
        return 'I\'m good!'

    if 'i love python' in processed:
        return 'Remember to subscribe!'

    return 'I don\'t understand'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get basic info of the incoming message
    message_type: str = update.message.chat.type
    text: str = update.message.text

    # Print a log for debugging
    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    # React to group messages only if users mention the bot directly
    if message_type == 'group':
        # Replace with your bot username
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return  # We don't want the bot respond if it's not mentioned in the group
    else:
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
    app.add_handler(CommandHandler("echo", echo_callback))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("tweet", tweet))
    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Log all errors
    app.add_error_handler(error)

    # print('Polling...')
    # Run the bot
    app.run_polling(poll_interval=0.2)
