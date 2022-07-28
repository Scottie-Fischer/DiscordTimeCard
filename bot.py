#------------------------------------------#
#   Created by Scott Fischer
#
#   This is a project that clocks user activity and stores it in a dataBase
#   
#------------------------------------------#

#Library Dependencies
import os
import discord
from dotenv import load_dotenv
import sqlite3

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def or_ready():
    print(f'{client.user} has connected to Discord!')

client.run(TOKEN)
