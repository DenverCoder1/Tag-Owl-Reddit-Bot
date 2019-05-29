import praw
import math
import datetime
import time
import re

from prawcore.exceptions import PrawcoreException
import praw.exceptions

import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

ME = "HogwartsTagOwl" # username

SUB = "ravenclaw+RavenclawsBookClub+arithmancy"

ArithmancySignupURL = "-----------------------------"
AssignmentsSignupURL = "------------------------------"
TagListSpreadsheetURL = "------------------------------"
ravenclaw_info_text2 = f'\n\n****\n\n*I\'m a bot. Do not reply here. | [About this bot](https://www.reddit.com/r/ravenclaw/wiki/meta/tagowl) | [Tag Lists]({TagListSpreadsheetURL}) | [Sign up / Opt-out]({AssignmentsSignupURL}) | [PM u\/eyl327](https://www.reddit.com/message/compose/?to=eyl327) if you have any questions.*'
arithmancy_info_text2 = f'\n\n****\n\n*I\'m a bot. Do not reply here. | [Sign up / Opt-out]({ArithmancySignupURL}) | [PM u\/eyl327](https://www.reddit.com/message/compose/?to=eyl327) if you have any questions.*'
ravenclaw_how_to_use = f'You have summoned {ME}.\n\nThe tag owl helps users in the tower notify large groups of users because Reddit does not send notifications when you mention more than 3 users at a time.\n\nTo use the tag owl, write a message in a comment or text submission and then add at the end, "Send by owl to" followed by a list all of the users you want to tag.\n\nIn a comment, you must have **at least 4** users mentioned to activate the owl. Reddit will send notifications if (and only if) there are 3 or fewer users in your comment.\n\nIn a text submission, however, you can send an owl to **1 or more** users because Reddit does **not** send notifications to users tagged in text submissions.\n\nExample usage:\n\n    I have an idea for the group assignment! Let me know what you think.    \n    Send by owl to u/username1, u/username2, u/username3, u/username4\n\nThis bot should not be used more than is necessary. Only tag people who have expressed interest in being tagged and don\'t use it too often. {ravenclaw_info_text2}'
arithmancy_how_to_use = f'The Tag Owl is a bot created by u/eyl327 which is used by the moderators of r/Arithmancy to tag a large list of users since Reddit doesn\'t send notifications when more than 3 users are mentioned in a single comment. Each user signed up will receive a Private Message when the owl is summoned. Sign up for notifications using [this form]({ArithmancySignupURL}).'+arithmancy_info_text2

r = praw.Reddit(client_id='-----------', client_secret="-------------------",
                     password='----------', user_agent=f'{ME} Bot by u/eyl327',
                     username=ME)

def oauthAuthenticate():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope) # get email and key from creds
    file = gspread.authorize(credentials) # authenticate with Google
    global sheet
    sheet = file.open("Sign Up for Assignment Reminders (Responses)").sheet1 # open sheet

def get_date(post):
    time = post.created_utc
    return datetime.datetime.fromtimestamp(time)

def get_user_status(currUsernameToCheck, post):
    try:
        if getattr(r.redditor(currUsernameToCheck), 'is_suspended', False):
            return "Account suspended"
        elif (f"{post.subreddit}"!="Arithmancy"):
            if len(list(r.subreddit(str(post.subreddit)).contributor.__call__(redditor=currUsernameToCheck))) == 0:
                return "Not an approved submitter"
    except praw.exceptions.APIException as err:
        print(err)
    else:
        return "Account exists"

def process_post(post, postType): # post can be a comment or submission // postType can be "comment" or "submission"
    if (not post.saved):
        post.save()
        print(f"Recieved {postType} in {post.subreddit} by {post.author} at {get_date(post)}")
        #####################################
        ## Notify of every new submission: ##
        #####################################
        if (postType=="submission"):
            url_link = f'http://www.reddit.com/r/{post.subreddit}/comments/{post.id}'
            errorsList = "Message was not sent to: "
            tries = 0
            all_cells = ""
            usernamesListed = False
            info_text2 = ravenclaw_info_text2
            while (usernamesListed == False):
                try:
                    usernames = []
                    if (f"{post.subreddit}"=="ravenclaw"):
                        all_cells = sheet.range('J2:J200')
                    elif (f"{post.subreddit}"=="TagBotTest"):
                        all_cells = sheet.range('A2:A200')  #Send message to eyl327 only (for testing)
                    else:
                        #all_cells = sheet.range('A2:A200')  #Send message to eyl327 only (for testing)
                        break
                    for cell in all_cells:
                        if (cell.value != ""):
                            usernames.append(cell.value)
                    if (usernames != []): #more than 0 usernames added
                        usernamesListed = True
                        usernamesLength = len(usernames)
                        for x in range(0,len(usernames)):
                            try:
                                currUsername = str(usernames[x][2:]) #remove 'u/' from username
                                currUserStatus = get_user_status(currUsername, post)
                                if (currUserStatus=="Account exists"):
                                    r.redditor(currUsername).message(f"There's a new post in r/{post.subreddit}",f"Hi u/{currUsername},\n\nThere's a new post in r/{post.subreddit}:\n\n>[**{str(post.title)}**]({url_link}) posted by u/{post.author} {info_text2}")
                                    print('\r', end='')
                                    print(f"Sent PM to {x+1}/{len(usernames)} users subscribed to r/{post.subreddit}", end='')
                                    print('\r', end='')
                                else:
                                    print(f"EXCEPTION: Failed to send message. {currUserStatus}.")
                                    x += 1
                                    errorsList += f"u/{currUsername} ({currUserStatus}), "
                                    usernamesLength -= 1
                            except praw.exceptions.APIException as err:
                                print(f"EXCEPTION: APIException - Failed to send message. {err}")
                                x += 1
                                errorsList += f"u/{currUsername} ({err}), "
                                usernamesLength -= 1
                            except Exception as err:
                                print(f"EXCEPTION: An error occured - Failed to send message. {err}")
                                x += 1
                                errorsList += f"u/{currUsername} ({err}), "
                                usernamesLength -=1
                        if (errorsList != "Message was not sent to: "): # has errors
                            errorsList = errorsList[:-2]
                            op = str(post.author)
                            r.redditor("eyl327").message('Bot failed to send message to users subscribed to every post', postType+': '+url_link+" by u/"+op+"\n\n"+errorsList+info_text2)
                        print("")
                        print(f"Sent PM to {usernamesLength} users subscribed to r/{post.subreddit}.")
                    else: #no usernames
                        print("EXCEPTION: usernames list is blank")
                        print(all_cells)
                        time.sleep(5)
                        tries += 1
                        if (tries>2):
                            break #exit loop without list
                except ConnectionError as err:
                    tries += 1
                    if (tries>2):
                        break #exit loop without list
                    print(f"EXCEPTION: ConnectionError - Failed to create username list. {err}")
                    time.sleep(5)
                except NameError as err:
                    tries += 1
                    if (tries>2):
                        break #exit loop without list
                    print(f"EXCEPTION: NameError - Failed to create username list. {err}")
                    oauthAuthenticate()
                    print("Gsheets Reauthenticated...")
                    time.sleep(2)
                except gspread.exceptions.APIError as err:
                    tries += 1
                    if (tries>2):
                        break #exit loop without list
                    print(f"EXCEPTION: gspread APIError - Failed to create username list. {err}")
                    oauthAuthenticate()
                    print("Gsheets Reauthenticated...")
                    time.sleep(2)
                except Exception as err:
                    tries += 1
                    if (tries>2):
                        break #exit loop without list
                    print(f"EXCEPTION: An error occured - Failed to create username list. {err}")
                    time.sleep(5)
        ######################################
        ## Check for "send by owl" request: ##
        ######################################
        if (postType=="submission"): #submission
            cbody = ' '+post.selftext
        else: #comment
            cbody = ' '+post.body
        ctexts = re.split('\s*send\W*(?:an)*(?:by)*(?:the)*(?:to)*(?:a)*\W*(?:Ravenclaw)*\W*(?:Tag)*\W*owl\W*(?:to)*\:*', cbody, flags=re.IGNORECASE)
        requests = len(ctexts)
        if (requests>1):
            while (requests>1):
                ctext = ' '+ctexts[requests-1]
                new_time = get_date(post)
                ##print(new_time)
                op = str(post.author)
                num_of_usernames = ctext.count(' u/')+ctext.count('/u/')+ctext.count(',u/')+ctext.count('&u/')+ctext.count('+u/')+ctext.count('.u/')+ctext.count('(u/')+ctext.count('\nu/')
                
                called_list = "you"
                info_text2 = ravenclaw_info_text2
                how_to_use = ravenclaw_how_to_use
                if (f"{post.subreddit}"=="Arithmancy"):
                    called_list = "the **Arithmancy List**"
                    info_text2 = arithmancy_info_text2
                    how_to_use = arithmancy_how_to_use
                elif (bool(re.search('(?:the)*\W*assignments?\W*(?:tag)*\W*list', ctext, flags=re.IGNORECASE))):
                    called_list = "the **Assignments List**"
                elif (bool(re.search('(?:the)*\W*dueling\W*(?:tag)*\W*list', ctext, flags=re.IGNORECASE))):
                    called_list = "the **Dueling List**"
                elif (bool(re.search('(?:the)*\W*intrahouse\W*(?:challenge?|challenges?)*\W*(?:tag)*\W*list', ctext, flags=re.IGNORECASE))):
                    called_list = "the **Intrahouse List**"
                elif (bool(re.search('(?:the)*\W*(?:hprankdown3?|hpr3?)\W*(?:betting)*\W*(?:tag)*\W*list', ctext, flags=re.IGNORECASE))):
                    called_list = "the **HPRankdown List**"
                if (bool(re.search('(?:the)*\W*test\W*(?:tag)*\W*list', ctext, flags=re.IGNORECASE))):
                    called_list = "the **Test List**"
                if (called_list != "you"): # called_list was changed to tag list
                    num_of_usernames = 999
                    print(called_list)
                else: # usernames are mentioned instead of list
                    ctext_start = ctext[:6] # first 6 characters of ctext
                    if (ctext_start.count('/') == 0): # There is a '/' (i.e. a username) in first 6 char of ctext
                        num_of_usernames = 0
                        print("Does not have username immediately after \"Send by owl\" request ("+ctext_start+"...)")
                        if (requests==2): #if last request in comment and not followed by usernames, look at whole comment
                            ctext = cbody
                            num_of_usernames = ctext.count(' u/')+ctext.count('/u/')+ctext.count(',u/')+ctext.count('&u/')+ctext.count('+u/')+ctext.count('.u/')+ctext.count('(u/')+ctext.count('\nu/')
                            print("Checking full comment for usernames...")
                        else: #notify me by PM
                            try:
                                if (postType=="submission"): #submission
                                    url_link = f'http://www.reddit.com/r/{post.subreddit}/comments/{post.id}'
                                else: #comment
                                    url_link = f'http://www.reddit.com/r/{post.subreddit}/comments/{str(post.link_id)[3:]}/-/{str(post.id)}'
                                r.redditor('eyl327').message('Bot did not any send messages', postType+': '+url_link+" by u/"+op+"\n\n"+"Does not have username immediately after \"Send by owl\" request ("+ctext_start+"...)"+info_text2)
                            except Exception as err:
                                print(f"EXCEPTION: An error occured - Failed to send message. {err}")
                hasTags = num_of_usernames > 0
                print(f"{new_time > last_time} {hasTags} ({num_of_usernames}) {op != ME}")
                #if (new_time > last_time): #if newer than the comment posted before starting
                if (True): # using "saved" instead of time
                    if (op != ME): #If not replying to self
                        if (hasTags): #if has more than ~3~ 0 users tagged
                            in_progress_comment = post.reply(f"Your owl will be sent shortly. If this message is not automatically deleted within a few minutes, notify u/eyl327. {info_text2}")

                            tries = 0
                            all_cells = ""
                            usernamesListed = False
                            while (usernamesListed == False):
                                try:
                                    usernames = []
                                    if (called_list == "the **Arithmancy List**"):
                                        #all_cells = sheet.range('A2:A200')  #Send message to eyl327 only (for testing)
                                        all_cells = sheet.range('R2:R200')
                                    elif (called_list == "the **Assignments List**"):
                                        #all_cells = sheet.range('A2:A200')  #Send message to eyl327 only (for testing)
                                        all_cells = sheet.range('B2:B200')
                                    elif (called_list == "the **Dueling List**"):
                                        #all_cells = sheet.range('A2:A200')  #Send message to eyl327 only (for testing)
                                        all_cells = sheet.range('D2:D200')
                                    elif (called_list == "the **Intrahouse List**"):
                                        #all_cells = sheet.range('A2:A200')  #Send message to eyl327 only (for testing)
                                        all_cells = sheet.range('F2:F200')
                                    elif (called_list == "the **HPRankdown List**"):
                                        #all_cells = sheet.range('A2:A200')  #Send message to eyl327 only (for testing)
                                        all_cells = sheet.range('H2:H200')
                                    elif (called_list == "the **Test List**"):
                                        all_cells = sheet.range('A2:A200')  #Send message to eyl327 only (for testing)
                                    else:
                                        ##num_of_comments = int(math.ceil(ctext.count('u/') / 3) - 1)
                                        newctext = ctext.replace(",u/"," u/").replace("/u/"," u/").replace("&u/"," u/").replace("+u/"," u/").replace("."," ").replace(","," ").replace("!"," ").replace("?"," ").replace("&"," ").replace("+"," ").replace("\""," ").replace(")"," ")
                                        ##usernames = [word+", " for word in newctext.split() if word.startswith('u/')]
                                        usernames = [word for word in newctext.split() if word.startswith('u/')]
                                        ##usernames.append("")
                                        ##usernames.append("")
                                        all_cells = "none"
                                        usernamesListed = True
                                    if (called_list != "you"):
                                        for cell in all_cells:
                                            if (cell.value != ""):
                                                usernames.append(cell.value)
                                        if (usernames != []): #more than 0 usernames added
                                            usernamesListed = True
                                        else: #list is empty
                                            print("EXCEPTION: usernames list is blank")
                                            print(all_cells)
                                            time.sleep(5)
                                            tries += 1
                                            if (tries>2):
                                                break #exit loop without list
                                except ConnectionError as err:
                                    tries += 1
                                    if (tries>2):
                                        break #exit loop without list
                                    print(f"EXCEPTION: ConnectionError - Failed to create username list. {err}")
                                    time.sleep(5)
                                except NameError as err:
                                    tries += 1
                                    if (tries>2):
                                        break #exit loop without list
                                    print(f"EXCEPTION: NameError - Failed to create username list. {err}")
                                    oauthAuthenticate()
                                    print("Gsheets Reauthenticated...")
                                    time.sleep(2)
                                except gspread.exceptions.APIError as err:
                                    tries += 1
                                    if (tries>2):
                                        break #exit loop without list
                                    print(f"EXCEPTION: gspread APIError - Failed to create username list. {err}")
                                    oauthAuthenticate()
                                    print("Gsheets Reauthenticated...")
                                    time.sleep(2)
                                except Exception as err:
                                    tries += 1
                                    if (tries>2):
                                        break #exit loop without list
                                    print(f"EXCEPTION: An error occured - Failed to create username list. {err}")
                                    time.sleep(5)

                            usernamesLength = len(usernames)

                            upage = f'http://www.reddit.com/user/{op}'
                            
                            if (postType=="submission"): #submission
                                url_link = f'http://www.reddit.com/r/{post.subreddit}/comments/{post.id}'
                            else: #comment
                                url_link = f'http://www.reddit.com/r/{post.subreddit}/comments/{str(post.link_id)[3:]}/-/{str(post.id)}'

                            if (called_list != "you"):
                                info_text1 = f'**[u\/{op}]({upage})** sent **[an owl]({url_link})** to {called_list}.'
                            else:
                                info_text1 = f'**[u\/{op}]({upage})** sent you **[an owl]({url_link})**.'
                            quote_text = '\n\n>'+ctexts[requests-2].replace("\n\n","\n\n>")

                            if (quote_text=='\n\n>'): # if no context provided
                                if (postType=="submission"): #submission
                                        quote_text = f"\n\n>[**{str(post.title)}**]({url_link})"
                                else: #comment
                                    if (str(post.link_id)[3:]==str(post.parent())): # replied to submission
                                        quote_text = f"\n\n>Message link: [**{str(post.link_title)}**](http://www.reddit.com/comments/{str(post.link_id)[3:]}) by u/{post.parent().author}"
                                    else: # replied to comment
                                        quote_text = f"\n\n>Message link: [**this comment**](http://www.reddit.com/comments/{str(post.link_id)[3:]}/-/{str(post.parent())}) by u/{post.parent().author}"

                            print(usernames)
                            errorsList = "Message was not sent to: "
                            for x in range(0,len(usernames)):
                                currUsername = str(usernames[x][2:]) #remove 'u/' from username
                                try:
                                    currUserStatus = get_user_status(currUsername, post)
                                    if (currUserStatus=="Account exists"):
                                        r.redditor(currUsername).message(f'{op} sent you an owl', f"Hi u/{currUsername},\n\n"+info_text1+quote_text+info_text2)
                                        print('\r', end='')
                                        print(f"Sent PM to {x+1}/{len(usernames)} users in {post.id} by {op} in {str(post.subreddit)}...", end='')
                                        print('\r', end='')
                                    else:
                                        print(f"EXCEPTION: Failed to send message. {currUserStatus}.")
                                        x += 1
                                        errorsList += f"u/{currUsername} ({currUserStatus}), "
                                        usernamesLength -= 1
                                except praw.exceptions.APIException as err:
                                    print(f"EXCEPTION: APIException - Failed to send message. {err}")
                                    x += 1
                                    errorsList += f"u/{currUsername} ({err}), "
                                    usernamesLength -= 1
                                except Exception as err:
                                    print(f"EXCEPTION: An error occured - Failed to send message. {err}")
                                    x += 1
                                    errorsList += f"u/{currUsername} ({err}), "
                                    usernamesLength -= 1
                            print("")
                            print(f"Sent PM to {usernamesLength} users in {post.id} by {op} in {str(post.subreddit)}.")
                            in_progress_comment.delete()
                            postedComment = False
                            while (postedComment == False):
                                try:
                                    if(usernamesLength == 0): #If message was sent to 0 people, PM me
                                        new_comment = post.reply(f"Your owl was sent to {usernamesLength} users."+info_text2)
                                        r.redditor("eyl327").message('Bot failed to send message', postType+': '+url_link+" by u/"+op+"\n\n"+"Sent to 0 users"+info_text2)
                                    elif (errorsList == "Message was not sent to: "): # no errors
                                        new_comment = post.reply(f"Your owl has been sent successfully to {usernamesLength} users."+info_text2)
                                    else: #If message was not sent to 1 or more users, PM me
                                        errorsList = errorsList[:-2]
                                        if (called_list != "you"):
                                            errorsList += f"\n\nAccounts which do not exist, have been deleted, or are not approved submitters of r/{post.subreddit} will be removed from all tag lists. If you added one of these accounts, please check the spelling and sign up again."
                                        new_comment = post.reply(f"Your owl has been sent successfully to {usernamesLength} users.\n\n"+errorsList+info_text2)
                                        r.redditor("eyl327").message('Bot failed to send message', postType+': '+url_link+" by u/"+op+"\n\n"+errorsList+info_text2)
                                    postedComment = True
                                except Exception as err:
                                    print(f"EXCEPTION: An error occured - Failed to comment. {err}")
                                    time.sleep(15)
                            print(f"Posted reply to {post.id} by {op} in {str(post.subreddit)}.")
                            time.sleep(10)
                            requests = 0
                        else:
                            if (postType=="submission"): #submission
                                url_link = f'http://www.reddit.com/r/{post.subreddit}/comments/{post.id}'
                            else: #comment
                                url_link = f'http://www.reddit.com/r/{post.subreddit}/comments/{str(post.link_id)[3:]}/-/{str(post.id)}'
                            r.redditor("eyl327").message('Bot wording mentioned', f"Detected invalid mention in {url_link} by {op} in {str(post.subreddit)}.")
                            #not enough tags
                            if (ctexts[requests-2].count('how')+ctexts[requests-2].count('How')+ctexts[requests-2].count('help') > 0):
                                post.reply(how_to_use)
                                print(f"Posted instructions to {post.id} by {op} in {str(post.subreddit)}.")
                                time.sleep(10)
                            else:
                                #post.reply("Sorry, I couldn't understand your request.")
                                #print(ctext)
                                print("Not asking how")
                requests = requests - 1
        else: print("Not a match.")

while True:
    global last_time
    subreddit = r.subreddit(SUB)
    CHECK_INTERVAL = 10 # seconds to wait before checking again
    COMMENT_LIMIT = 30 # number of comments to check
    SUBMISSION_LIMIT = 10 # number of submissions to check
    restart = True
    running = True
    while running:
        try:
            if restart == True:
                for comment in r.redditor(ME).comments.new(limit=1):
                    last_time = get_date(comment)
                    print(f"Logged in: {str(datetime.datetime.now())[:-7]}")
                    print(f"Last comment: {last_time}")
                    print(f"Timezone: {time.tzname[time.localtime().tm_isdst]}")
                    oauthAuthenticate()
                    print("Gsheets authenticated")
                    print(f"Subreddit: {SUB}")
                    print(f"Checking last {COMMENT_LIMIT} comments and {SUBMISSION_LIMIT} submissions every {CHECK_INTERVAL} seconds...")
                    restart = False
                    break
            #print(f"Checking last {COMMENT_LIMIT} comments and {SUBMISSION_LIMIT} submissions...")
            for comment in r.redditor(ME).comments.new(limit=1):
                last_time = get_date(comment)
            for comment in subreddit.comments(limit=COMMENT_LIMIT):
                process_post(comment,"comment")
            for submission in subreddit.new(limit=SUBMISSION_LIMIT):
                process_post(submission,"submission")
            #print(f"Waiting {CHECK_INTERVAL} seconds")
            time.sleep(CHECK_INTERVAL)
        except PrawcoreException as err:
            print(f"EXCEPTION: PrawcoreException. {err}")
            time.sleep(15)
            restart = True
        except Exception as err:
            print(f"EXCEPTION: An error occured. {err}")
            time.sleep(15)
            restart = True