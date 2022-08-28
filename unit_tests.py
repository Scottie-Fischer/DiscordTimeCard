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

def serialize(strings):
    ser = ""
    first = True
    for string in strings:
        if not first:
            ser = ser + "_._"
            first = False
        ser = ser + string 
    return ser

def deserialize(string):
    return string.split("_._")

def test_ready():
    q = 'select exists (select 1 from server_configs' +\
        ' where id=? collate nocase) limit 1'
    guilds = {"Server2"}
    for guild in guilds:
        new_server = server_obj(guild)
        
        query = conn.execute(q,(guild,))

        #Check if servers are in the DB
        if query.fetchone()[0] == 1:
            q = 'select {} from server_configs where id=? collate nocase'

            #Get all the data from the database
            games    = conn.execute(q.format('games'),\
                    (guild,)).fetchone()[0]
            un_users = conn.execute(q.format('untracked_users'),\
                    (guild,)).fetchone()[0]
            channel  = conn.execute(q.format('channel'),\
                    (guild,)).fetchone()[0]
            to_zone  = curr.execute(q.format('to_zone'),\
                    (guild,)).fetchone()[0]

            un_users = deserialize(un_users)
            games = deserialize(games)

            print("Current tz for " + guild + " ->> " + to_zone)
            to_zone = time.tzname[time.daylight]
            new_zone = tz.gettz(to_zone)

            new_time = datetime.now().astimezone(new_zone)
            print("Clocked at: " + new_time.strftime("%H%M%S"))

            #Setup the data for the server_object
            new_server.set_fields(games,un_users,channel,to_zone)

        else:
            #Not in DB so we create a table for it and configs remain default
            new_server.create_table()
            comm = 'INSERT INTO server_configs '+\
            '(id,games,untracked_users,channel,to_zone)'+\
            'VALUES(?,?,?,?,?)'

            users = ""
            games = "Minecraft"
            to_zone = (str)(time.tzname[time.daylight])
            print("Current tz for " + guild + " -> " + to_zone)
            conn.execute(comm,(guild,games,users,'general',to_zone))
            conn.commit()

        server_map[guild] = new_server

    print(f'Unit Tests does not connect to Discord!')

test_ready()

#Main Function:
while(True):
    func = input("Please input a function:\n")
    match(func):
        case("clk in"):
            guild = server_map["Server2"]
            user = "Scottie#5328"
            time = datetime.now()
            res = guild.get_times(time)
            utc_time = res[0]
            loc_time = res[1]
            loc_str = loc_time.strftime("%H%M%S")
            guild.clock_in(user,loc_str)
            print(user + " clocked in: " + loc_time.strftime("%H:%M:%S %p"))
        case("clk out"):
            guild = server_map["Server2"]
            user = "Scottie#5328"

        #----Auto Time Detection----
            #time = datetime.now()
            #res = guild.get_times(time)
            #utc_time = res[0]
            #loc_time = res[1]
            #loc_str = loc_time.strftime("%H%M%S")
        #----Manual Time Detection----
            loc_str = input("Input Time format %H%M%S: ")
        #-----------------------------

            res = guild.clock_out(user,loc_str)
            msg = "Earned {:.5f} hours, total: {:.5f}"
            msg = msg.format(res[0],res[1])
            print(user + " clocked out: " + loc_time.strftime("%H:%M:%S %p"))
            print(msg)
        case("fix clock"):
            guild = server_map["Server2"]
            time = input("Enter a Time.\nFormat is HH:MM:SS ")
            loc_time = strptime(time,"%H:%M:%S")
            loc_zone = guild.get_zone
            loc_time.replace(tzinfo=loc_zone)
            utc_time = loc_time.astimezone(tz.tzutc())
            loc_str = loc_time.strftime("%H%M%S")
        case("add game"):
            print("Not Implemented")
        case("remove game"):
            print("Not Implemented")
        case("take lunch"):
            print("Not Implemented")
        case("quit"):
            break
    
