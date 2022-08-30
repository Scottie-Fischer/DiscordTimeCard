import discord
import os
import sqlite3
from dotenv import load_dotenv
from datetime import datetime
from dateutil import tz
import pytz
import time
from enum import Enum

from server import server_obj

server_map = {}

#-----------Setting Up Bot------------
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intentss = discord.Intents().default()
intentss.members = True
intentss.presences = True
intentss.guilds = True
client = discord.Client(intents = intentss)

#-----------Default DB TABLE----------------
conn = sqlite3.connect('timecards.db')
curr = conn.cursor()
try:
    #This table will hold the settings each server sets
    #This is in case the bot goes down we dont want to lose info
    conn.execute('''CREATE TABLE IF NOT EXISTS server_configs
            (id TEXT, games TEXT, untracked_users TEXT,
             channel TEXT, to_zone TEXT)''')

    conn.execute('''CREATE TABLE IF NOT EXISTS default_name 
            (id TEXT, start TEXT, end TEXT, total REAL, pto REAL)''')

except Exception as e:
    print("Error making default table: " + str(e))


@client.event
async def on_ready():
    q = 'select exists (select 1 from server_configs' +\
        ' where id=? collate nocase) limit 1'

    for guild in client.guilds:
        new_server = server_obj(guild.name)
        
        #Check if servers are in the DB
        if (new_server.check_server()):
            #We call the objects method to pull data from the DB
            new_server.build_from_db()
            
        else:
            #Not in DB so we call the objects method to create a new table
            new_server.create_table()

        server_map[guild.name] = new_server

    print(f'Test Version of {client.user} has connected to Discord!')

@client.event
async def on_guild_join(new_guild):
    new_server = server_obj(new_guild.name)
    new_server.create_table()
    server_map[new_guild.name] = new_server
    print(f"Created new server: {new_guild.name}")

#This will handle all the commands for the bot
#Commands:
#clk in         - clks user in manually
#clk out        - clks user out manually
#fix clk        - setting a new clk in manually
#timezone       - tells what the guilds timezone is
#set timezone   - sets guilds timezone
#timezone help  - DMs the user all timezones 
#add game       - adds a game to track for guild
#del game       - removes a tracked game for guild
#take lunch     - 
#add PTO
#sub PTO
@client.event
async def on_message(message):
    #Basic info from the message
    user = message.author
    msg = message.content
    chan = message.channel
    time = message.created_at

    #Make sure we dont respond to the bot's own msg 
    if user == client.user:
        return

    #Get the server_obj from map, will be used in most commands
    guild = server_map[message.guild.name]
    channel = message.guild.get_channel(guild.get_channel())
    
    if channel == None:
        await message.channel.send("Guild does not have a channel for the Bot")
        return 

    #Clock In Functionality------------------------------------------
    if msg.startswith("$clk in"):
        
        #Turn utc time in server's local time
        times = guild.get_times(time)
        time_str = times[1].strftime("%H%M%S")      #Time formatted for DB
        time_prt = times[1].strftime("%H:%M:%S %p") #Time formatted for print
        
        #Use Server_obj method to clock out user
        guild.clock_in(user,time_str)

        #Message server with response
        await message.channel.send(user.name + " clocked in at " + time_prt)
    
    #Clock Out Functionality-----------------------------------------
    elif msg.startswith("$clk out"):
        
        #Turn utc time into server's local time
        times = guild.get_times(time)
        time_str = times[1].strftime("%H%M%S")      #Time formatted for DB
        time_prt = times[1].strftime("%H:%M:%S %p") #Time formatted for print
        res = guild.clock_out(user,time_str)
        
        #Check if clock out failed
        msg = user.name + " clocked out: " + time_ptr
        msg = msg + " \nEarned: {%0.5f} hours, total: {%0.5f} hours"
        msg = msg.format(res[0],res[1])
        
        if res == ('-1','-1'):
            #Failed so we update msg for error
            msg = 'Sorry you have to clock in before you clock out'
        await message.channel.send(msg)
    
    #Manually Fix Clock Functionality--------------------------------
    elif msg.startswith("$fix clk"):
        await message.channel.send("No Functionality yet")
  
    #Displaying what games are being tracked for the server
    elif msg.startswith("get games"):
        games = guild.get_games()

        await channel.send("Server is tracking: " + str(games))

    #Adding a Game for the server to track
    elif msg.startswith("$add game"):
        new_game = msg.split("$add game")[1][1:]
        guild.add_game(new_game)
        games = guild.get_games()
        
        await channel.send("Now tracking games: " + str(games))
   
    #Remove a Game from the Tracked Games
    elif msg.startswith("$del game"):
        old_game = msg.split("del game")[1][1:]
        guild.del_game(old_game)
        games = guild.get_Games()

        await channel.send("Now tracking games: " + str(games))

    #Getting Timezone from Server------------------------------------
    elif msg.startswith("$timezone"):
        guild = server_map[message.guild.name]
        zone = guild.get_zone()
        await message.channel.send("This servers timezone: " + zone)
    
    #Manually Set the Guild's Local Timezone-------------------------
    elif msg.startswith("$set timezone"):
        guild = server_map[message.guild.name]
        zone = msg.split("$set timezone")[1][1:]
        if guild.set_tz(zone):
            #Was good timezone
            timezone = pytz.timezone(zone)
            time = datetime.now().astimezone(timezone).strftime("%H:%M:%S")
            await chan.send("Setting timezone, current time: " + time)
        else:
            await chan.send("Time zone is not valid. Please use Olson Format")
            await chan.send("For Help use command: $timezone help")

    #Help With Timezone Format---------------------------------------
    elif msg.startswith("$timezone help"):
        zones = ""
        for timezone in pytz.all_timezones:
            zones = zones + timezone + "\n"
        await user.send(zones)

@client.event
async def on_member_update(before,after):
    guild = before.guild

    print(before.name + " updated activity in " + guild.name)

client.run(TOKEN)
