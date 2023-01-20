import datetime
from dotenv import load_dotenv
import asyncpraw
import os
import discord
import asyncio
from datetime import datetime



"""
Using AsyncPRAW to stream comments and submissions
made to a subreddit. If a new submission is detected
the bot will reply with a comment listing all the
possible keywords that will be counted.
If a new comment is detected the script will determine if
the comment contains one of the specified keywords and if
it does it will update the comment displaying all the votes.

Currently the bot is rescanning all existing comments of a
submission to update the score. It would be more effective to
store the counts for every submission
in a .json file but I currently do not have
the time to implement that.

@author https://github.com/yanik-recke
"""

load_dotenv('variablesforpost.env')  # get log-ins from .env-file
client_id = os.getenv('REDDITID')
client_secret = os.getenv('REDDITSECRET')
username = os.getenv('REDDITUSERNAME')
password = os.getenv('REDDITPASSWORD')

key0 = os.getenv('KEY0')
key1 = os.getenv('KEY1')
key2 = os.getenv('KEY2')

maintainer = os.getenv('MAINTAINER')

subreddit = os.getenv('SUBREDDIT')

async def main():
    # oauth
    reddit = asyncpraw.Reddit(client_id=client_id,
                      client_secret=client_secret,
                      username=username,
                      password=password,
                      user_agent='xqRAwasDwx998')

    # setting "checking for validation" to true
    reddit.validate_on_submit = True

    subreddits = await reddit.subreddit(subreddit)
    
    print('Logged in as:')
    print(await reddit.user.me())

    # begin streams
    await asyncio.gather(streamSubmissions(reddit, subreddits), streamComments(reddit, subreddits))


async def streamSubmissions(reddit, subreddits):
    print('streaming submissions')
    stream = subreddits.stream.submissions(skip_existing = True, pause_after = -1)

    #main loop
    while True:
        try:
            async for submission in stream:
                if submission is None:
                    break
                
                time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                # post comment with formatting
                comment = await submission.reply("Current verdict: __To be determined__\n\nLast updated on " + time +
                                       "\n\nPossible verdicts are: "+ key0 + ", " + key1 + ", " + key2 + "\n\nCheck back when there are more comments!")
                await comment.mod.distinguish(sticky=True)
            

        # Error handling
        except Exception as err0:
            print('[SUBMISSIONS]: Connection down')
            error = False
            print(err0)  
            await asyncio.sleep(20)
                
            #reconnect
            while error == False:
                try:
                    #reinitiate stream
                    stream = subreddits.stream.submissions(skip_existing=True,pause_after = -1)
                    error = True
                    user = await reddit.redditor(maintainer)
                    await user.message('Status: Timed out', '[SUBMISSIONS] Bot back online')

                except (Exception) as err1:
                    #log
                    print('Trying to reconnect')
                    await asyncio.sleep(60)


async def streamComments(reddit, subreddits):
    print('streaming comments')
    stream = subreddits.stream.comments(skip_existing = True, pause_after = -1)
    me = await reddit.user.me()
    
    while True:
        try:
            async for comment in stream:
                if comment is None:
                    break

                # check if contains keyword and is not made by bot -> update post
                if (comment.author != me.name):
                    
                    submission = comment.submission
                    await submission.load()
                    #BIDA, KAH, NDA
                    votes = [0, 0, 0]
                    
                    for com in submission.comments:
                        if (com.author == me):
                            bots_comment = com
                            continue
            
                        elif key0 in com.body:
                            votes[0] = votes[0] + 1
                        elif key1 in com.body:
                            votes[1] = votes[1] + 1
                        elif key2 in com.body:
                            votes[2] = votes[2] + 1
                            
                    # calculating which has the most mentions
                    if (votes[0] > votes[1]):
                        verdict = key0
                        if (votes[0] < votes[2]):
                            verdict = key2
                    elif (votes[1] < votes[2]):
                        verdict = key2
                    else:
                        verdict = key1
                    

                    msg = """Bezeichnung | Anzahl 
:--:|:--:
"""
                    msg += key0 + "|" + str(votes[0]) + "\n"
                    msg += key1 + "|" + str(votes[1]) + "\n"
                    msg += key2 + "|" + str(votes[2]) + "\n\n"
                    
                    await bots_comment.edit("Current verdict: >!" + verdict + "!<\n\n" +
                                            "Last updated on: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + "\n\n" + msg +
                                            "\n *** \n ^(Ich bin ein Bot.)")

        # Error handling
        except(Exception) as err0:
            print('[COMMENTS]: Connection down')
            error = False
            print(err0)  
            await asyncio.sleep(20)
                
            #reconnect
            while error == False:
                try:
                    #reinitiate stream
                    stream = subreddits.stream.comments(skip_existing=True, pause_after = -1)
                    user = await reddit.redditor(maintainer)
                    await user.message('Status: Timed out', '[COMMENTS] Bot back online')
                    error = True

                except (Exception) as err1:
                    #log
                    print('Trying to reconnect')
                    await asyncio.sleep(60)


asyncio.run(main())
