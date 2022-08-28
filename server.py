#Class Helper Functions
from datetime import datetime
from dateutil import tz
import pytz
import sqlite3

def get_times(datetime,to_zone):
    utc_time = datetime.strftime('%H%M%S')
    loc_time = datetime.replace(tzinfo=from_zone)
    loc_time = datetime.astimezone(to_zone).strftime("%I:%M%:%S %p")
    return (utc_time, loc_time)

class server_obj:
    #Fields
    name = ""            #Guild name
    games = []           #Tracked games
    untracked_users = [] #Users opting out of bot
    channel = 'general'
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    conn = sqlite3.connect('timecards.db')

    #Ctor
    def __init__(self,name):
        self.name = name
        self.games = ["Minecraft"]
        self.untracked_users = []
        self.channel = 'general'
    
    def set_fields(self,games,untracked_users,channel,to_zone):
        self.games = games
        self.untracked_users = untracked_users
        self.channel = channel
        self.to_zone = tz.gettz(to_zone)    

    #Class Methods

    def get_zone(self):
        return self.to_zone

    def get_times(self,utc_time):
        utc_time.replace(tzinfo=self.from_zone)
        loc_time = utc_time.astimezone(self.to_zone)
        return (utc_time,loc_time)

    def create_table(self):
        comm =  'CREATE TABLE IF NOT EXISTS {}'.format(self.name) + \
                '(id TEXT, start TEXT, end TEXT, total REAL, pto REAL)'

        try:
            self.conn.execute(comm)
            print(f'Created new table: {self.name}')
        except Exception as e:
            print(f"Error in making table: {e} \n")

    def check_user(self,user):
        q = 'select exists (select 1 from {} '.format(self.name) + \
            'where id=? collate nocase) limit 1'
        query = self.conn.execute(q,(user,))
        if query.fetchone()[0] == 1:
            return True
        else:
            return False

    def set_channel(self,name):
        self.channel = name

    def set_tz(self,timezone):
        if timezone not in pytz.all_timezones:
            return 0
        self.to_zone = timezone
        comm =  'UPDATE server_configs SET to_zone=?'+\
                'WHERE id=? collate nocase'
        self.conn.execute(comm,(timezone,self.name))
        self.conn.commit()
        return 1

    #This function clock in a specific user
    #Assumptions: Args are both strings
    def clock_in(self,username,time_in):

        #Check if user does not want to be tracked
        if username not in self.untracked_users:
            
            #Check if user is in database
            if(self.check_user(username)):
                
                #User Exists so we update the DB
                comm = 'UPDATE {} '.format(self.name) + \
                       'SET start=? WHERE id=? collate nocase'
                self.conn.execute(comm,(time_in,username))
            #self.conn.commit()
            
            else:
                #User Does Not Exist so we insert new id
                comm =  'INSERT INTO {}'.format(self.name) +\
                        '(id,start,total,pto)' +\
                        'VALUES(?,?,?,?)'
                self.conn.execute(comm,(username,time_in,0,0))
            self.conn.commit()

    #This function logs user clock out time, and calculates PTO

    def clock_out(self,user,time_out):
        comm = 'select {} from {} where id=? collate nocase'
        
        #Get stored data from DB
        time_in = self.conn.execute(comm.format('start',self.name)\
                 ,(user,)).fetchone()[0]
        #Old PTO
        pto_o = self.conn.execute(comm.format('pto',self.name)\
                 ,(user,)).fetchone()[0]
        #Old total time
        tot_o = self.conn.execute(comm.format('total',self.name)\
                 ,(user,)).fetchone()[0]

        #Check if they have clocked in before
        if time_in == '-1': return ('-1','-1')

        #Extract ints from string
        hrs_in  = (int)(time_in[0:2])
        hrs_out = (int)(time_out[0:2])
        
        min_in  = (int)(time_in[2:4])
        min_out = (int)(time_out[2:4])

        sec_in  = (int)(time_in[4:6])
        sec_out = (int)(time_out[4:6])

        #Account for rollover of 24hr clock
        if(hrs_out < hrs_in): hrs_out += 24
        if(min_out < min_in): min_out += 60
        if(sec_out < sec_in): sec_out += 60

        hrs_t = hrs_out - hrs_in
        min_t = min_out - min_in
        sec_t = sec_out - sec_in
        
        #Earned Time as Hours
        tot_e = hrs_t + (min_t/60) + (sec_t/3600)
        #Earned PTO
        pto_e = tot_e * 0.062
        #Total PTO Hours
        pto_t = pto_e + pto_o
        #Total Hours Worked
        tot_t = tot_e + tot_o

        if(self.check_user(user)):
            self.conn.execute('''UPDATE {} SET start=?,end=?,total=?,pto=?
                                 WHERE id=? collate nocase'''.format(self.name)\
                                 ,('-1',time_out,tot_t,pto_t,user))
            self.conn.commit()
            return (pto_e,pto_t)
        else:
            return ('-1','-1')







