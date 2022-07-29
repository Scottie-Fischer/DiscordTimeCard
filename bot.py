#------------------------------------------#
#   Created by Scott Fischer
#
#   This is a project that clocks user activity and stores it in a dataBase
#   
#------------------------------------------#

#Library Dependencies
import os
import discord
import sqlite3
from dateutil import tz
from dotenv import load_dotenv


from_zone = tz.tzutc()
to_zone = tz.tzlocal()


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

async def parse_message(message):
    time = ''
    for char in message:
        if char.isnumeric():
            time += char

    print(time)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    message_low = message.content.lower();
    if message.author == client.user:
        return
    if ('clock in' in message_low) | ('clocking in' in message_low):
        await parse_message(message_low)
        
        #Get time the message was sent (This is given in UTC time)
        datetime = message.created_at

        #We format the datetime object to formatted string
        utc_time = datetime.strftime('%H%M%S')

        #Now we want to convert to local time
        #The datetime is niave so we tell it its in UTC
        loc_time = datetime.replace(tzinfo=from_zone)
        
        loc_time = loc_time.astimezone(to_zone).strftime('%I:%M:%S %p')
        
        #Get the Sender's Name
        user_sending = message.author.name
        
        #Send a message to the channel
        await message.channel.send(user_sending + ', thanks for clocking in at ' + loc_time + '!')
        
        #Now we want to add the start time to the DB
        

client.run(TOKEN)
