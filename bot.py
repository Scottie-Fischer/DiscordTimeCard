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

#------------DB SETUP------------------
conn = sqlite3.connect('timecards.db')
curr = conn.cursor()

try:
    #conn.execute('''CREATE TABLE IF NOT EXISTS TIMECARDS 
    #            (user TEXT PRIMARY KEY,
    #            in TEXT, out TEXT,
    #            total_hours REAL NOT NULL,
    #            pto REAL NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS timecards
                 (id Text, start TEXT, end TEXT, total REAL, pto REAL)''')

except Exception as e:
    print("Table already exists" + str(e))
#--------------------------------------

async def parse_message(message):
    time = ''
    for char in message:
        if char.isnumeric():
            time += char

    print(time)

async def add_clock_in(user,time_in):
    print("TIME IN: " + time_in)
    hours = time_in[0:2]
    mins  = time_in[2:4]
    secs  = time_in[4:6]
    print("Hours: " + hours + " Mins: " + mins + " Secs: " + secs)
    
    #We query 
    query = curr.execute('select exists (select 1 from timecards where id=? collate nocase) limit 1',(user,))
    if query.fetchone()[0] == 1:
        #Exists
        #conn.execute('INSERT INTO timecards (id,start) VALUES(?,?)',(user,time_in))
        conn.execute('UPDATE timecards SET start=?  WHERE id=? collate nocase',(time_in,user))

    else:
        #Does not exist
        conn.execute('INSERT INTO timecards (id,start,total,pto) VALUES(?,?,?,?)',(user,time_in,0,0))

    conn.commit()

async def clock_out(user, time_outs):
    time_out = input("GIVE A  TIME PLS: ")
    #We want to convert the times to ints and find the difference
    time_in = curr.execute('select start from timecards where id=? collate nocase',(user,)).fetchone()[0]
    old_PTO = curr.execute('select pto from timecards where id=? collate nocase',(user,)).fetchone()[0]
    old_total = curr.execute('select total from timecards where id=? collate nocase',(user,)).fetchone()[0]

    hours = abs(int(time_out[0:2]) - int(time_in[0:2]))
    mins  = abs(int(time_out[2:4]) - int(time_in[2:4]))
    secs  = abs(int(time_out[4:6]) - int(time_in[4:6]))

    total_hours = hours + (mins/60) + (secs/3600)
    #print("OUT : " + time_out)
    #print("WORKED FOR: " + str(hours) + " mins: " + str(mins) + " secs: " + str(secs))

    earned_PTO = (hours * 0.062) + (mins/60 * 0.062) + (secs/3600 * 0.062)
    new_PTO = earned_PTO + old_PTO
    
    new_total = old_total + total_hours

    query = curr.execute('select exists (select 1 from timecards where id=? collate nocase) limit 1',(user,))
    if query.fetchone()[0] == 1:
        #Exists
        #curr.execute('INSERT INTO timecards (user,end,total,pto) VALUES(?,?,?,?)',(user,time_out,))
        curr.execute('''UPDATE timecards SET end=?,total=?,pto=? 
                     WHERE id=? collate nocase''',(time_out,new_total,new_PTO,user)) 
    conn.commit()

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
        
        user = message.author.name

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
        await add_clock_in(user,utc_time)
    if ('clock out' in message_low) | ('clocking out' in message_low):
        user = message.author.name
        
        datetime = message.created_at
        
        utc_time = datetime.strftime('%H%M%S')

        loc_time = datetime.replace(tzinfo=from_zone)

        loc_time = loc_time.astimezone(to_zone).strftime('%I:%M:%S %p')

        await message.channel.send(user + ', clocking out at ' + loc_time + '?')

        await clock_out(user,utc_time)

client.run(TOKEN)
