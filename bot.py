#------------------------------------------#
#   Created by Scott Fischer
#
#   This is a project that clocks user activity 
#   and stores it in a SQL dataBase. It then
#   calculates PTO of hours clocked and responds
#   to users in the same channel
#   
#------------------------------------------#

#Library Dependencies
import os
import discord
import sqlite3
import random
from datetime import datetime
from dateutil import tz
from dotenv import load_dotenv
from enum import Enum

#Constants
from_zone = tz.tzutc()
to_zone = tz.tzlocal()

#-----------Setting Up Bot------------
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intentss = discord.Intents().default()
intentss.members = True
intentss.presences = True
client = discord.Client(intents = intentss)

#------------DB SETUP------------------
conn = sqlite3.connect('timecards.db')
curr = conn.cursor()

try:

    conn.execute('''CREATE TABLE IF NOT EXISTS timecards
                 (id Text, start TEXT, end TEXT, total REAL, pto REAL)''')

except Exception as e:
    print("Error in making table: " + str(e) + "\n")
#--------------------------------------

#Read from the prompts txt and fill an array with quotes
prompts = open("prompts.txt",'r')

Quotes = prompts.readlines()
#-------------------------------------------------------


#--------------Helper Functions-------------------------

def check_db_user(user):
    q = 'select exists (select 1 from timecards where id=? collate nocase) limit 1'
    query = curr.execute(q,(user,))
    
    if query.fetchone()[0] == 1:
        return True
    else:
        return False


async def parse_message(message):
    time = ''
    for char in message:
        if char.isnumeric():
            time += char

    print(time)

async def clock_in(user,time_in):
    
    if (check_db_user(user)):
        #Exists so we Update the DB instead of inserting
        conn.execute('''UPDATE timecards SET start=?  
                    WHERE id=? collate nocase''',(time_in,user))

    else:
        #Does not exist so we insert new employee id
        conn.execute('''INSERT INTO timecards 
                    (id,start,total,pto) 
                    VALUES(?,?,?,?)''',(user,time_in,0,0))

    conn.commit()

def clock_out(user, time_out):
    
    #We want to convert the times to ints and find the difference
    time_in = curr.execute('select start from timecards where id=? collate nocase'\
                            ,(user,)).fetchone()[0]
    old_PTO = curr.execute('select pto from timecards where id=? collate nocase'\
                            ,(user,)).fetchone()[0]
    old_total = curr.execute('select total from timecards where id=? collate nocase'\
                            ,(user,)).fetchone()[0]
    if time_in == '-1':
        #print('Must clock in before clocking out')
        return (0.0,0.0)

    #Extract hours, mins, and seconds from strings
    hours = abs(int(time_out[0:2]) - int(time_in[0:2]))
    mins  = abs(int(time_out[2:4]) - int(time_in[2:4]))
    secs  = abs(int(time_out[4:6]) - int(time_in[4:6]))

    #Calculate time in hours
    total_hours = hours + (mins/60) + (secs/3600)
    
    #Calculate PTO using 0.062 as ratio of PTO
    earned_PTO = (hours * 0.062) + (mins/60 * 0.062) + (secs/3600 * 0.062)
    new_PTO = earned_PTO + old_PTO
    
    new_total = old_total + total_hours
    #q = 'select exists (select 1 from timecards 
    #where id=? collate nocase) limit 1'
    #query = curr.execute(q,(user,))
    if (check_db_user(user)):
        #User exists so we update Database
        curr.execute('''UPDATE timecards SET start=?,end=?,total=?,pto=? 
                     WHERE id=? collate nocase'''\
                     ,('-1',time_out,new_total,new_PTO,user)) 
    
    conn.commit()
    return (earned_PTO,new_PTO)

def get_times(datetime):
    #Get time from the message
    #datetime = message.created_at
    
    #Convert UTC time to String
    utc_time = datetime.strftime('%H%M%S')
    
    #Tell UTC time it is in UTC bc it is niave to begin
    local = datetime.replace(tzinfo=from_zone)
    
    #Convert UTC to local time and get string
    loc_time = local.astimezone(to_zone).strftime("%I:%M:%S %p")

    return (utc_time,loc_time)

def take_lunch(message):
    user = message.author
    

#----------------------Event Handling----------------------------------

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    message_low = message.content.lower();
    if message.author == client.user:
        return
    
    if message_low == 'lunch break':
        take_lunch(message)

    if 'fix clock' in message_low:
        user = message.author.name
        await message.channel.send("Sounds like an issue not an iss-me\n- Corporate")
        numbers = ''
        for char in message_low:
            if char.isnumeric():
                numbers+=char
        
        #have to transfer from pst to utc then store in DB
        #+7 hours
        loc_time = datetime.strptime(numbers,"%H%M")
        loc_time = loc_time.replace(tzinfo=to_zone)
        utc_time = loc_time.astimezone(from_zone).strftime('%H%M%S')
        print('UTC: ' + utc_time)

        curr.execute('''UPDATE timecards SET start=? WHERE id=? collate nocase''',(utc_time,user))

        await message.channel.send("Fixing Clock_In to: " + loc_time.strftime("%H:%M:%S"))

        return

    if ('clock in' in message_low) | ('clocking in' in message_low):
        await parse_message(message_low)
        
        user = message.author.name
 
        #Get the Sender's Name
        #user_sending = message.author.name
       
        #Get Times from Message
        #times = get_times(message)
        times = get_times(message.created_at)

        utc_time = times[0]
        loc_time = times[1]

        #Send a message to the channel
        msg = user + ', thanks for clocking in at ' + loc_time + '!'
        await message.channel.send(msg)
        
        #Now we want to add the start time to the DB
        await clock_in(user,utc_time)
    if ('clock out' in message_low) | ('clocking out' in message_low):
        
        user = message.author.name
        
        #Get  Times from Message
        #times = get_times(message)
        times = get_times(message.created_at)

        utc_time = times[0]
        loc_time = times[1]
        #-------------------------------

        #Get a random motivational quote
        indx = random.randint(0,len(Quotes)-1)
        motivation = Quotes[indx]

        #Removed the newline char from the string
        motivation = motivation[:(len(motivation)-1)]

        #Add times to DB and calculate PTO
        PTO = clock_out(user,utc_time)

        #Check for clocking out before clocking in
        if((PTO[0] == 0.0) & (PTO[1] == 0.0)):
            await message.channel.send(user + " you must clock in first.")
        
        else:
            await message.channel.send(user + ', clocking out at ' + loc_time \
                                    + ' already?\nRemember %s' % motivation \
                                    + '!\n - From Corporate')
            #Send PTO message
            await message.channel.send('Earned %.5f' \
                                        %PTO[0] + \
                                        ' hours of PTO, %.5f total hours PTO'\
                                        % PTO[1])

@client.event
async def on_member_update(before,after):
    
    if before.guild.name != 'Quarantine South':
        return

    befor_acts = before.activities
    after_acts =  after.activities
    
    pre_check  = False
    post_check = False
    
    game = discord.Activity()
    
    user = before.name

    for acts in after_acts:
        if acts.type == discord.ActivityType.playing:
            post_check = True
            game = acts
    
    for acts in befor_acts:
        if acts.type == discord.ActivityType.playing:
            pre_check = True
            game = acts 

    if len(befor_acts) > len(after_acts) and ((pre_check) and (not post_check)):
        if game.name == 'Minecraft':
            
            times = get_times(game.start)
            print(after.name + " clocked out at " + times[1])
            
            utc_time = times[0]
            loc_time = times[1]

            indx = random.randint(0,len(Quotes)-1)
            motivation = Quotes[indx]

            #Removed the newline char from the string
            motivation = motivation[:(len(motivation)-1)]

            #Add times to DB and calculate PTO
            PTO = clock_out(user,utc_time)

            channels = before.guild.channels
            general = channels[0]
            for channel in channels:
                if(channel.type == discord.ChannelType.text) \
                & (channel.name == 'general'):
                    general = channel

            #Check for clocking out before clocking in
            if((PTO[0] == 0.0) & (PTO[1] == 0.0)):
                await general.send(user + " you must clock in first.")

            else:
                msg = user + ',clocking out at ' + loc_time \
                    + 'already?\nRemember %s' % motivation  \
                    + '!\n - From Corporate'
                await general.send(msg)
                #Send PTO message
                msg = 'Earned %0.5f ' %PTO[0] + \
                      ' hours of PTO, %0.5f total hours PTO' %PTO[1])
                await general.send(msg)


    elif len(befor_acts) < len(after_acts) and ((not pre_check) and (post_check)):
        if game.name == 'Minecraft':
            
            user = before.name
            times = get_times(game.start)

            utc_time = times[0]
            loc_time = times[1]

            await clock_in(user,utc_time)

            msg = user + ' thanks for clocking in at ' + loc_time + '!'

            channels = before.guild.channels
            general = channels[0]
            for channel in channels:
                if(channel.type == discord.ChannelType.text) \
                & (channel.name == 'general'):
                    general = channel
            
            await general.send(msg)

            #print("Would insert msg into: " + server)

            #print(after.name + " clocked in at " + times[1])

client.run(TOKEN)
