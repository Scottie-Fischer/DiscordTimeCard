# DiscordTimeCard
This is a discord bot that will store and calculate hours worked by scraping messages and activity. 
On a 'clock in' message it will send a message response in discord and store the time of message in the SQL database. Then on a 'clock out' message it will store that time and calculate PTO earned and total accrued PTO. It will then send a message response.
However, a message is not required and the bot will scan for user activity changes and automatically clock in and clock out for users when they start playing certain games.

Language: Python

Major Libraries:
- Discord.py
- Sqlite3
- dotenv
