import praw
import datetime
import time
import re

from prawcore.exceptions import PrawcoreException
import praw.exceptions

import gspread
from oauth2client.service_account import ServiceAccountCredentials

ME = "HogwartsTagOwl"

TEST_SUB = "tagbottest"
MAIN_SUBS = "ravenclaw+RavenclawsBookClub+Arithmancy+Dueling+tagbottest"

SUBREDDIT = MAIN_SUBS # Make sure this is set to MAIN_SUBS to work in production

TagListSpreadsheetURL = "URL_REMOVED"
ArithmancySignupURL = "URL_REMOVED"
DuelingSignupURL = "URL_REMOVED"
AssignmentsSignupURL = "URL_REMOVED"
arith_sign_up_promo = f"\n\nWant to receive notifications about new puzzles and announcements? Fill out [this form]({ArithmancySignupURL})!"
dueling_sign_up_promo = f"\n\nWant to receive notifications when the home game opens? Fill out [this form]({DuelingSignupURL})!"
ravenclaw_info_text2 = "\n\n****\n\n*I'm a bot. Do not reply here. | [About this bot](https://www.reddit.com/r/ravenclaw/wiki/meta/tagowl) | [Tag Lists](URL_REMOVED) | [Sign up / Opt-out](URL_REMOVED) | [PM u\/denvercoder01](https://www.reddit.com/message/compose/?to=denvercoder01) if you have any questions.*"
arithmancy_info_text2 = "\n\n****\n\n*I'm a bot. Do not reply here. | [Sign up / Opt-out](URL_REMOVED) | [PM u\/denvercoder01](https://www.reddit.com/message/compose/?to=denvercoder01) if you have any questions.*"
dueling_info_text2 = "\n\n****\n\n*I'm a bot. Do not reply here. | [Sign up / Opt-out](URL_REMOVED) | [PM u\/denvercoder01](https://www.reddit.com/message/compose/?to=denvercoder01) if you have any questions.*"
ravenclaw_how_to_use = f'You have summoned {ME}.\n\nThe tag owl helps users in the tower notify large groups of users because Reddit does not send notifications when you mention more than 3 users at a time.\n\nTo use the tag owl, write a message in a comment or text submission and then add at the end, "Send by owl to" followed by a list all of the users you want to tag.\n\nIn a comment, you must have **at least 4** users mentioned to activate the owl. Reddit will send notifications if (and only if) there are 3 or fewer users in your comment.\n\nIn a text submission, however, you can send an owl to **1 or more** users because Reddit does **not** send notifications to users tagged in text submissions.\n\nExample usage:\n\n    I have an idea for the group assignment! Let me know what you think.    \n    Send by owl to u/username1, u/username2, u/username3, u/username4\n\nThis bot should not be used more than is necessary. Only tag people who have expressed interest in being tagged and don\'t use it too often. {ravenclaw_info_text2}'
arithmancy_how_to_use = (
    "The Tag Owl is a bot created by u/denvercoder01 which is used by the moderators of r/Arithmancy to tag a large list of users since Reddit doesn't send notifications when more than 3 users are mentioned in a single comment. Each user signed up will receive a Private Message when the owl is summoned. Sign up for notifications using [this form](https://docs.google.com/forms/d/e/1FAIpQLSexzdmni3rVswAxjrVGq7tYYEDYekVDqLy-QGy7btHOqluhwA/viewform)."
    + arithmancy_info_text2
)
dueling_how_to_use = (
    "The Tag Owl is a bot created by u/denvercoder01 which is used by the hosts of r/Dueling to tag a large list of users since Reddit doesn't send notifications when more than 3 users are mentioned in a single comment. Each user signed up will receive a Private Message when the owl is summoned. Sign up for notifications using [this form](https://docs.google.com/forms/d/e/1FAIpQLSemT5CybFt1k6CJc31RLH2PI3Q7xYaDYqskSHhJtnGsMiLhhg/viewform)."
    + dueling_info_text2
)

r = praw.Reddit(
    client_id="CLIENT_ID_REMOVED",
    client_secret="CLIENT_SECRET_REMOVED",
    password="PASSWORD_REMOVED",
    user_agent=f"{ME} Bot by u/denvercoder01",
    username=ME,
)


def oauth_authenticate():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "creds.json", scope
    )  # get email and key from creds
    file = gspread.authorize(credentials)  # authenticate with Google
    global sheet
    sheet = file.open(
        "Sign Up for Assignment Reminders (Responses)"
    ).sheet1  # open sheet


def get_date(post):
    time = post.created_utc
    return datetime.datetime.fromtimestamp(time)


def is_approved_submitter(username, sub):
    matching_contributors = r.subreddit(str(sub)).contributor.__call__(
        redditor=username
    )
    return len(list(matching_contributors)) != 0


def get_user_status(curr_username, post):
    try:
        if getattr(r.redditor(curr_username), "is_suspended", False):
            return "Account suspended"
        elif (
            f"{post.subreddit}" != "Arithmancy"
            and f"{post.subreddit}" != "Dueling"
            and f"{post.subreddit}" != "TagBotTest"
            and not is_approved_submitter(curr_username, post.subreddit)
        ):
            return "Not an approved submitter"
    except praw.exceptions.APIException as err:
        print(err)
    else:
        return "Account exists"


def get_usernames(called_list, ctext):
    tries = 0
    usernames = []
    usernames_listed = False
    while usernames_listed == False:
        try:
            usernames = []
            if called_list == "the **Arithmancy List**":
                all_cells = sheet.range("R2:R300")
            elif called_list == "the **Hogwarts Dueling List**":
                all_cells = sheet.range("T2:T1000")
            elif called_list == "the **Assignments List**":
                all_cells = sheet.range("B2:B300")
            elif called_list == "the **Dueling List**":
                all_cells = sheet.range("D2:D300")
            elif called_list == "the **Intrahouse List**":
                all_cells = sheet.range("F2:F200")
            elif called_list == "the **HPRankdown List**":
                all_cells = sheet.range("H2:H200")
            elif called_list == "the **Test List**":
                all_cells = sheet.range("A2:A200")
            else:
                ctext_no_links = re.sub(
                    r"https?:\/\/[^\)\s\r\n]+", "", ctext, flags=re.MULTILINE
                )
                newctext = (
                    ctext_no_links.replace(",u/", " u/")
                    .replace("/u/", " u/")
                    .replace("&u/", " u/")
                    .replace("+u/", " u/")
                    .replace("+u/", " u/")
                    .replace("(u/", " u/")
                    .replace("[u/", " u/")
                    .replace("\\_", "_")
                    .replace(".", " ")
                    .replace(",", " ")
                    .replace("!", " ")
                    .replace("?", " ")
                    .replace("&", " ")
                    .replace("+", " ")
                    .replace('"', " ")
                    .replace(")", " ")
                    .replace("]", " ")
                )
                usernames = [word for word in newctext.split() if word.startswith("u/")]
                all_cells = "none"
                usernames_listed = True
            if called_list != "you":
                for cell in all_cells:
                    if cell.value != "":
                        usernames.append(cell.value)
                if usernames != []:  # more than 0 usernames added
                    usernames_listed = True
                else:  # list is empty
                    print("EXCEPTION: usernames list is blank")
                    print(all_cells)
                    time.sleep(5)
                    tries += 1
                    if tries > 2:
                        break  # exit loop without list
        except ConnectionError as err:
            tries += 1
            if tries > 2:
                break  # exit loop without list
            print(f"EXCEPTION: ConnectionError - Failed to create username list. {err}")
            time.sleep(5)
        except NameError as err:
            tries += 1
            if tries > 2:
                break  # exit loop without list
            print(f"EXCEPTION: NameError - Failed to create username list. {err}")
            oauth_authenticate()
            print("Gsheets Reauthenticated...")
            time.sleep(2)
        except gspread.exceptions.APIError as err:
            tries += 1
            if tries > 2:
                break  # exit loop without list
            print(
                f"EXCEPTION: gspread APIError - Failed to create username list. {err}"
            )
            oauth_authenticate()
            print("Gsheets Reauthenticated...")
            time.sleep(2)
        except Exception as err:
            tries += 1
            if tries > 2:
                break  # exit loop without list
            print(
                f"EXCEPTION: An error occured - Failed to create username list. {err}"
            )
            time.sleep(5)
    return usernames


def send_pms(usernames, post, op, info_text1, quote_text, info_text2, dueling=False):
    errors_list = "Message was not sent to: "
    usernames_length = len(usernames)
    for x in range(0, len(usernames)):
        curr_username = str(usernames[x][2:])  # remove 'u/' from username
        try:
            curr_user_status = get_user_status(curr_username, post)
            if curr_user_status == "Account exists":
                if dueling:
                    r.redditor(curr_username).message(
                        "The home quiz is now open!",
                        f"Hi u/{curr_username},\n\n"
                        + info_text1
                        + quote_text
                        + info_text2,
                    )
                else:
                    r.redditor(curr_username).message(
                        f"{op} sent you an owl",
                        f"Hi u/{curr_username},\n\n"
                        + info_text1
                        + quote_text
                        + info_text2,
                    )
                print("\r", end="")
                print(
                    f"Sent PM to {x+1}/{len(usernames)} users in {post.id} by {op} in {str(post.subreddit)}...",
                    end="",
                )
                print("\r", end="")
            else:
                print(f"EXCEPTION: Failed to send message. {curr_user_status}.")
                x += 1
                errors_list += f"u/{curr_username} ({curr_user_status}), "
                usernames_length -= 1
        except praw.exceptions.APIException as err:
            print(f"EXCEPTION: APIException - Failed to send message. {err}")
            # wait for ratelimit to go away (temporary fix)
            if bool(re.search("try again in \d+", f"{err}", flags=re.IGNORECASE)):
                print("retrying in 4.5 minutes")
                time.sleep(270)
                try:
                    r.redditor(curr_username).message(
                        f"{op} sent you an owl",
                        f"Hi u/{curr_username},\n\n"
                        + info_text1
                        + quote_text
                        + info_text2,
                    )
                    print("\r", end="")
                    print(
                        f"Sent PM to {x+1}/{len(usernames)} users in {post.id} by {op} in {str(post.subreddit)}...",
                        end="",
                    )
                    print("\r", end="")
                except praw.exceptions.APIException as err:
                    print(f"EXCEPTION x2: APIException - Failed to send message. {err}")
                    x += 1
                    errors_list += f"u/{curr_username} ({err}), "
                    usernames_length -= 1
                except Exception as err:
                    print(
                        f"EXCEPTION x2: An error occured - Failed to send message. {err}"
                    )
                    x += 1
                    errors_list += f"u/{curr_username} ({err}), "
                    usernames_length -= 1
            else:
                x += 1
                errors_list += f"u/{curr_username} ({err}), "
                usernames_length -= 1
        except Exception as err:
            print(f"EXCEPTION: An error occured - Failed to send message. {err}")
            x += 1
            errors_list += f"u/{curr_username} ({err}), "
            usernames_length -= 1
    return {"usernamesLength": usernames_length, "errorsList": errors_list}


def post_reply_comment(
    usernames_length,
    post,
    errors_list,
    called_list,
    post_type,
    url_link,
    op,
    info_text2,
):
    posted_comment = False
    while posted_comment == False:
        try:
            if usernames_length == 0:  # If message was sent to 0 people, PM me
                post.reply(
                    f"Your owl was sent to {usernames_length} users." + info_text2
                )
                try:
                    r.redditor("denvercoder01").message(
                        "Bot failed to send message",
                        post_type
                        + ": "
                        + url_link
                        + " by u/"
                        + op
                        + "\n\n"
                        + "Sent to 0 users"
                        + info_text2,
                    )
                except Exception as err:
                    print(
                        f"EXCEPTION: An error occured - Failed to message errors at completion. {err}"
                    )
            elif errors_list == "Message was not sent to: ":  # no errors
                post.reply(
                    f"Your owl has been sent successfully to {usernames_length} users."
                    + info_text2
                )
            else:  # If message was not sent to 1 or more users, PM me
                errors_list = errors_list[:-2]
                if called_list != "you":
                    errors_list += f"\n\nAccounts which do not exist, have been deleted, or are not approved submitters of r/{post.subreddit} will be removed from all tag lists. If you added one of these accounts, please check the spelling and sign up again."
                post.reply(
                    f"Your owl has been sent successfully to {usernames_length} users.\n\n"
                    + errors_list
                    + info_text2
                )
                try:
                    r.redditor("denvercoder01").message(
                        "Bot failed to send message",
                        post_type
                        + ": "
                        + url_link
                        + " by u/"
                        + op
                        + "\n\n"
                        + errors_list
                        + info_text2,
                    )
                except Exception as err:
                    print(
                        f"EXCEPTION: An error occured - Failed to message errors at completion. {err}"
                    )
            posted_comment = True
        except Exception as err:
            print(f"EXCEPTION: An error occured - Failed to comment. {err}")
            # too long error
            if bool(re.search("TOO_LONG", f"{err}", flags=re.IGNORECASE)):
                try:
                    r.redditor("denvercoder01").message(
                        "Bot failed to send message",
                        post_type
                        + ": "
                        + url_link
                        + " by u/"
                        + op
                        + "\n\nTOO_LONG error.",
                    )
                except Exception as err:
                    print(
                        f"EXCEPTION: An error occured - Failed to message errors at completion. {err}"
                    )
                break
            time.sleep(15)


# post can be a comment or submission
# postType can be "comment" or "submission"
def process_post(post, post_type):
    if not post.saved:
        post.save()
        print(
            f"Recieved {post_type} in {post.subreddit} by {post.author} at {get_date(post)}"
        )
        #####################################
        ## Notify of every new submission: ##
        #####################################
        if post_type == "submission":
            url_link = f"http://www.reddit.com/r/{post.subreddit}/comments/{post.id}"
            errors_list = "Message was not sent to: "
            tries = 0
            all_cells = ""
            usernames_listed = False
            info_text2 = ravenclaw_info_text2
            in_progress_comment = None
            # set post comment for arithmancy posts
            if f"{post.subreddit}" == "Arithmancy":
                info_text2 = arithmancy_info_text2
                in_progress_comment = post.reply(
                    f"Your message will be sent by owl shortly. If this message is not automatically deleted within a few minutes, notify u/denvercoder01. {info_text2}"
                )
            while usernames_listed == False:
                try:
                    usernames = []
                    if f"{post.subreddit}" == "ravenclaw":
                        all_cells = sheet.range("J2:J200")  # every post list
                    elif f"{post.subreddit}" == "Arithmancy":
                        all_cells = sheet.range("R2:R200")  # arithmancy list
                    elif f"{post.subreddit}" == "RavenclawsBookClub":
                        # Send message to denvercoder01 only (for testing)
                        all_cells = sheet.range("A2:A200")
                    elif f"{post.subreddit}" == "TagBotTest":
                        # Send message to denvercoder01 only (for testing)
                        all_cells = sheet.range("A2:A200")
                    else:
                        break
                    for cell in all_cells:
                        if cell.value != "":
                            usernames.append(cell.value)
                    if usernames != []:  # more than 0 usernames added
                        usernames_listed = True
                        usernames_length = len(usernames)
                        for x in range(0, len(usernames)):
                            # remove 'u/' from username
                            curr_username = str(usernames[x][2:])
                            try:
                                curr_user_status = get_user_status(curr_username, post)
                                if curr_user_status == "Account exists":
                                    r.redditor(curr_username).message(
                                        f"There's a new post in r/{post.subreddit}",
                                        f"Hi u/{curr_username},\n\nThere's a new post in r/{post.subreddit}:\n\n>[**{str(post.title)}**]({url_link}) posted by u/{post.author} {info_text2}",
                                    )
                                    print("\r", end="")
                                    print(
                                        f"Sent PM to {x+1}/{len(usernames)} users subscribed to r/{post.subreddit}",
                                        end="",
                                    )
                                    print("\r", end="")
                                else:
                                    print(
                                        f"EXCEPTION: Failed to send message. {curr_user_status}."
                                    )
                                    x += 1
                                    errors_list += (
                                        f"u/{curr_username} ({curr_user_status}), "
                                    )
                                    usernames_length -= 1
                            except praw.exceptions.APIException as err:
                                print(
                                    f"EXCEPTION: APIException - Failed to send message. {err}"
                                )
                                # wait for ratelimit to go away (temporary fix)
                                if bool(
                                    re.search(
                                        "try again in \d+",
                                        f"{err}",
                                        flags=re.IGNORECASE,
                                    )
                                ):
                                    print("retrying in 4.5 minutes")
                                    time.sleep(270)
                                    try:
                                        r.redditor(curr_username).message(
                                            f"There's a new post in r/{post.subreddit}",
                                            f"Hi u/{curr_username},\n\nThere's a new post in r/{post.subreddit}:\n\n>[**{str(post.title)}**]({url_link}) posted by u/{post.author} {info_text2}",
                                        )
                                        print("\r", end="")
                                        print(
                                            f"Sent PM to {x+1}/{len(usernames)} users subscribed to r/{post.subreddit}",
                                            end="",
                                        )
                                        print("\r", end="")
                                    except praw.exceptions.APIException as err:
                                        print(
                                            f"EXCEPTION x2: APIException - Failed to send message. {err}"
                                        )
                                        x += 1
                                        errors_list += f"u/{curr_username} ({err}), "
                                        usernames_length -= 1
                                    except Exception as err:
                                        print(
                                            f"EXCEPTION x2: An error occured - Failed to send message. {err}"
                                        )
                                        x += 1
                                        errors_list += f"u/{curr_username} ({err}), "
                                        usernames_length -= 1
                                else:
                                    x += 1
                                    errors_list += f"u/{curr_username} ({err}), "
                                    usernames_length -= 1
                            except Exception as err:
                                print(
                                    f"EXCEPTION: An error occured - Failed to send message. {err}"
                                )
                                x += 1
                                errors_list += f"u/{curr_username} ({err}), "
                                usernames_length -= 1
                        if errors_list != "Message was not sent to: ":  # has errors
                            errors_list = errors_list[:-2]
                            op = str(post.author)
                            r.redditor("denvercoder01").message(
                                "Bot failed to send message to users subscribed to every post",
                                post_type
                                + ": "
                                + url_link
                                + " by u/"
                                + op
                                + "\n\n"
                                + errors_list
                                + info_text2,
                            )
                        print("")
                        print(
                            f"Sent PM to {usernames_length} users subscribed to r/{post.subreddit}."
                        )
                        # post comment on arithmancy posts
                        if f"{post.subreddit}" == "Arithmancy":
                            op = str(post.author)
                            in_progress_comment.delete()
                            posted_comment = False
                            while posted_comment == False:
                                try:
                                    # If message was sent to 0 people, PM me
                                    if usernames_length == 0:
                                        post.reply(
                                            f"Your message was sent to {usernames_length} users."
                                            + info_text2
                                        )
                                        r.redditor("denvercoder01").message(
                                            "Bot failed to send message",
                                            post_type
                                            + ": "
                                            + url_link
                                            + " by u/"
                                            + op
                                            + "\n\n"
                                            + "Sent to 0 users"
                                            + info_text2,
                                        )
                                    elif (
                                        errors_list == "Message was not sent to: "
                                    ):  # no errors
                                        post.reply(
                                            f"Your message has been sent successfully by owl to {usernames_length} users.\n\n"
                                            + arith_sign_up_promo
                                            + info_text2
                                        )
                                    else:  # If message was not sent to 1 or more users, PM me
                                        errors_list += f"\n\nAccounts which do not exist, have been deleted, or are not approved submitters of r/{post.subreddit} will be removed from all tag lists. If you added one of these accounts, please check the spelling and sign up again."
                                        post.reply(
                                            f"Your owl has been sent successfully to {usernames_length} users.\n\n"
                                            + errors_list
                                            + info_text2
                                        )
                                    posted_comment = True
                                except Exception as err:
                                    print(
                                        f"EXCEPTION: An error occured - Failed to comment. {err}"
                                    )
                                    # too long error
                                    if bool(
                                        re.search(
                                            "TOO_LONG", f"{err}", flags=re.IGNORECASE
                                        )
                                    ):
                                        r.redditor("denvercoder01").message(
                                            "Bot failed to send message",
                                            post_type
                                            + ": "
                                            + url_link
                                            + " by u/"
                                            + op
                                            + "\n\nTOO_LONG error.",
                                        )
                                        break
                                    time.sleep(15)
                            print(
                                f"Posted reply to {post.id} by {op} in {str(post.subreddit)}."
                            )
                    else:  # no usernames
                        print("EXCEPTION: usernames list is blank")
                        print(all_cells)
                        time.sleep(5)
                        tries += 1
                        if tries > 2:
                            break  # exit loop without list
                except ConnectionError as err:
                    tries += 1
                    if tries > 2:
                        break  # exit loop without list
                    print(
                        f"EXCEPTION: ConnectionError - Failed to create username list. {err}"
                    )
                    time.sleep(5)
                except NameError as err:
                    tries += 1
                    if tries > 2:
                        break  # exit loop without list
                    print(
                        f"EXCEPTION: NameError - Failed to create username list. {err}"
                    )
                    oauth_authenticate()
                    print("Gsheets Reauthenticated...")
                    time.sleep(2)
                except gspread.exceptions.APIError as err:
                    tries += 1
                    if tries > 2:
                        break  # exit loop without list
                    print(
                        f"EXCEPTION: gspread APIError - Failed to create username list. {err}"
                    )
                    oauth_authenticate()
                    print("Gsheets Reauthenticated...")
                    time.sleep(2)
                except Exception as err:
                    tries += 1
                    if tries > 2:
                        break  # exit loop without list
                    print(
                        f"EXCEPTION: An error occured - Failed to create username list. {err}"
                    )
                    time.sleep(5)

        ######################################
        ## Check for "send by owl" request: ##
        ######################################
        if post_type == "submission":  # submission
            cbody = " " + post.selftext
        else:  # comment
            cbody = " " + post.body
        ctexts = re.split(
            "\s*send\W*(?:an)*(?:by)*(?:the)*(?:to)*(?:a)*\W*(?:Ravenclaw)*\W*(?:Tag)*\W*owl\W*(?:to)*\:*",
            cbody,
            flags=re.IGNORECASE,
        )
        requests = len(ctexts)
        op = str(post.author)
        if requests > 1:
            while requests > 1:
                ctext = " " + ctexts[requests - 1]
                new_time = get_date(post)
                num_of_usernames = (
                    ctext.count(" u/")
                    + ctext.count("/u/")
                    + ctext.count(",u/")
                    + ctext.count("&u/")
                    + ctext.count("+u/")
                    + ctext.count(".u/")
                    + ctext.count("(u/")
                    + ctext.count("\nu/")
                )

                called_list = "you"
                info_text2 = ravenclaw_info_text2
                how_to_use = ravenclaw_how_to_use
                # set info text
                if (
                    f"{post.subreddit}" == "Dueling"
                    or f"{post.subreddit}" == "TagBotTest"
                ):
                    info_text2 = dueling_info_text2
                    how_to_use = dueling_how_to_use
                elif f"{post.subreddit}" == "Arithmancy":
                    info_text2 = arithmancy_info_text2
                    how_to_use = arithmancy_how_to_use
                # if subreddit is arithmancy and not mentioning usernames, set tag list to Arithmancy
                if f"{post.subreddit}" == "Arithmancy" and num_of_usernames < 3:
                    called_list = "the **Arithmancy List**"
                # if subreddit is dueling and not mentioning usernames, set tag list to Hogwarts Dueling
                elif (
                    f"{post.subreddit}" == "Dueling"
                    or f"{post.subreddit}" == "TagBotTest"
                ) and num_of_usernames < 3:
                    called_list = "the **Hogwarts Dueling List**"
                # if not arithmancy/dueling tag, check for Ravenclaw tag list
                elif bool(
                    re.search(
                        "(?:the)*\W*assignments?\W*(?:tag)*\W*list",
                        ctext,
                        flags=re.IGNORECASE,
                    )
                ):
                    called_list = "the **Assignments List**"
                elif bool(
                    re.search(
                        "(?:the)*\W*dueling\W*(?:tag)*\W*list",
                        ctext,
                        flags=re.IGNORECASE,
                    )
                ):
                    called_list = "the **Dueling List**"
                elif bool(
                    re.search(
                        "(?:the)*\W*intrahouse\W*(?:challenge?|challenges?)*\W*(?:tag)*\W*list",
                        ctext,
                        flags=re.IGNORECASE,
                    )
                ):
                    called_list = "the **Intrahouse List**"
                elif bool(
                    re.search(
                        "(?:the)*\W*(?:hprankdown3?|hpr3?)\W*(?:betting)*\W*(?:tag)*\W*list",
                        ctext,
                        flags=re.IGNORECASE,
                    )
                ):
                    called_list = "the **HPRankdown List**"
                elif bool(
                    re.search(
                        "(?:the)*\W*test\W*(?:tag)*\W*list", ctext, flags=re.IGNORECASE
                    )
                ):
                    called_list = "the **Test List**"
                if called_list != "you":  # called_list was changed to tag list
                    num_of_usernames = 999
                    print(called_list)
                else:  # usernames are mentioned instead of list
                    ctext_start = ctext[:6]  # first 6 characters of ctext
                    # There is a '/' (i.e. a username) in first 6 char of ctext
                    if ctext_start.count("/") == 0:
                        num_of_usernames = 0
                        print(
                            'Does not have username immediately after "Send by owl" request ('
                            + ctext_start
                            + "...)"
                        )
                        # if last request in comment and not followed by usernames, look at whole comment
                        if requests == 2:
                            ctext = cbody
                            num_of_usernames = (
                                ctext.count(" u/")
                                + ctext.count("/u/")
                                + ctext.count(",u/")
                                + ctext.count("&u/")
                                + ctext.count("+u/")
                                + ctext.count(".u/")
                                + ctext.count("(u/")
                                + ctext.count("\nu/")
                            )
                            print("Checking full comment for usernames...")
                        else:  # notify me by PM
                            try:
                                if post_type == "submission":  # submission
                                    url_link = f"http://www.reddit.com/r/{post.subreddit}/comments/{post.id}"
                                else:  # comment
                                    url_link = f"http://www.reddit.com/r/{post.subreddit}/comments/{str(post.link_id)[3:]}/-/{str(post.id)}"
                                r.redditor("denvercoder01").message(
                                    "Bot did not any send messages",
                                    post_type
                                    + ": "
                                    + url_link
                                    + " by u/"
                                    + op
                                    + "\n\n"
                                    + 'Does not have username immediately after "Send by owl" request ('
                                    + ctext_start
                                    + "...)"
                                    + info_text2,
                                )
                            except Exception as err:
                                print(
                                    f"EXCEPTION: An error occured - Failed to send message. {err}"
                                )
                has_tags = num_of_usernames > 0
                print(
                    f"{new_time > last_time} {has_tags} ({num_of_usernames}) {op != ME}"
                )
                # if (new_time > last_time): #if newer than the comment posted before starting
                if op != ME:  # If not replying to self
                    if has_tags:  # if has more than ~3~ 0 users tagged
                        in_progress_comment = post.reply(
                            f"Your owl will be sent shortly. If this message is not automatically deleted within a few minutes, notify u/denvercoder01. {info_text2}"
                        )

                        usernames = get_usernames(called_list, ctext)

                        upage = f"http://www.reddit.com/user/{op}"

                        if post_type == "submission":  # submission
                            url_link = f"http://www.reddit.com/r/{post.subreddit}/comments/{post.id}"
                        else:  # comment
                            url_link = f"http://www.reddit.com/r/{post.subreddit}/comments/{str(post.link_id)[3:]}/-/{str(post.id)}"

                        if called_list != "you":
                            info_text1 = f"**[u\/{op}]({upage})** sent **[an owl]({url_link})** to {called_list}."
                        else:
                            info_text1 = f"**[u\/{op}]({upage})** sent you **[an owl]({url_link})**."
                        quote_text = "\n\n>" + ctexts[requests - 2].replace(
                            "\n\n", "\n\n>"
                        )

                        if quote_text == "\n\n>":  # if no context provided
                            if post_type == "submission":  # submission
                                quote_text = f"\n\n>[**{str(post.title)}**]({url_link})"
                            else:  # comment
                                # replied to submission
                                if str(post.link_id)[3:] == str(post.parent()):
                                    quote_text = f"\n\n>Message link: [**{str(post.link_title)}**](http://www.reddit.com/comments/{str(post.link_id)[3:]}) by u/{post.parent().author}"
                                else:  # replied to comment
                                    quote_text = f"\n\n>Message link: [**this comment**](http://www.reddit.com/comments/{str(post.link_id)[3:]}/-/{str(post.parent())}) by u/{post.parent().author}"

                        print(usernames)
                        pms = send_pms(
                            usernames, post, op, info_text1, quote_text, info_text2
                        )
                        usernames_length = pms["usernamesLength"]
                        errors_list = pms["errorsList"]
                        print("")
                        print(
                            f"Sent PM to {usernames_length} users in {post.id} by {op} in {str(post.subreddit)}."
                        )
                        in_progress_comment.delete()
                        post_reply_comment(
                            usernames_length,
                            post,
                            errors_list,
                            called_list,
                            post_type,
                            url_link,
                            op,
                            info_text2,
                        )
                        print(
                            f"Posted reply to {post.id} by {op} in {str(post.subreddit)}."
                        )
                        time.sleep(10)
                        requests = 0
                    else:
                        if post_type == "submission":  # submission
                            url_link = f"http://www.reddit.com/r/{post.subreddit}/comments/{post.id}"
                        else:  # comment
                            url_link = f"http://www.reddit.com/r/{post.subreddit}/comments/{str(post.link_id)[3:]}/-/{str(post.id)}"
                        r.redditor("denvercoder01").message(
                            "Bot wording mentioned",
                            f"Detected invalid mention in {url_link} by {op} in {str(post.subreddit)}.",
                        )
                        # not enough tags
                        if (
                            ctexts[requests - 2].count("how")
                            + ctexts[requests - 2].count("How")
                            + ctexts[requests - 2].count("help")
                            > 0
                        ):
                            post.reply(how_to_use)
                            print(
                                f"Posted instructions to {post.id} by {op} in {str(post.subreddit)}."
                            )
                            time.sleep(10)
                        else:
                            print("Not asking how")
                requests = requests - 1
        #########################################
        ## Check for dueling live game comment ##
        #########################################
        elif (
            f"{post.subreddit}" == "Dueling" or f"{post.subreddit}" == "TagBotTest"
        ) and post_type != "submission":
            top_level = str(post.link_id)[3:] == str(post.parent())
            mods = list(r.subreddit(f"{post.subreddit}").moderator())
            is_mod = post.author in mods
            # if replied to submission (comment is top level) and from a mod
            if top_level and is_mod:
                # Don't post if there is already a post from ClawTagger less than X days ago
                DATE_INTERVAL = 3
                last_post = list(r.redditor("ClawTagger").submissions.new(limit=1))[0]
                days_since_last_post = (
                    (time.time() - last_post.created_utc) / 60 / 60 / 24
                )
                # if has not posted anything in the last {DATE_INTERVAL(3)} days with exception of very recent post
                if days_since_last_post > DATE_INTERVAL or days_since_last_post < 0.02:
                    print(
                        str(days_since_last_post > DATE_INTERVAL) + " " + str(op != ME)
                    )
                    if ("The Live Game is OVER!" in cbody) and (op != ME):
                        called_list = "the **Hogwarts Dueling List**"
                        upage = "http://www.reddit.com/user/" + op
                        url_link = (
                            "http://www.reddit.com/comments/"
                            + str(post.link_id)[3:]
                            + "/-/"
                            + str(post.id)
                        )
                        info_text1 = (
                            "\n\n["
                            + op
                            + "]("
                            + upage
                            + ") just [**posted a link**]("
                            + url_link
                            + ") to this week's [r/Dueling](https://www.reddit.com/r/Dueling/) trivia game!\n\n"
                        )
                        url_search = re.compile("HOME QUIZ IS \[HERE\]\((.*)\)").search(
                            cbody
                        )
                        if url_search:
                            quiz_url = url_search.group(1)
                        else:
                            quiz_url = "[TBA]"
                        theme_search = re.compile("THEME: (.*)!").search(
                            str(post.link_title)
                        )
                        if theme_search:
                            quiz_theme = theme_search.group(1)
                        else:
                            quiz_theme = "[TBA]"
                        end_date_search = re.compile("open until (.*)\n").search(cbody)
                        if end_date_search:
                            end_date = end_date_search.group(1)
                            end_date = end_date.replace("*", "")
                            end_date = end_date.strip()
                        else:
                            end_date = "[TBA]"
                        # if all info found
                        if (
                            end_date != "[TBA]"
                            and quiz_theme != "[TBA]"
                            and quiz_url != "[TBA]"
                        ):
                            quote_text = f'Click on [**this link**]({quiz_url}) to start the quiz. The theme this week is **"{quiz_theme}!"** The quiz will be open until **{end_date}**'
                            in_progress_comment = post.reply(
                                f"Your owl will be sent shortly. If this message is not automatically deleted within a few minutes, notify u/denvercoder01. {dueling_info_text2}"
                            )
                            usernames = get_usernames(called_list, "")
                            pms = send_pms(
                                usernames,
                                post,
                                op,
                                info_text1,
                                quote_text,
                                dueling_info_text2,
                                dueling=True,
                            )
                            usernames_length = pms["usernamesLength"]
                            errors_list = pms["errorsList"]
                            print("")
                            print(
                                f"Sent PM to {usernames_length} users in {post.id} by {op} in {str(post.subreddit)}."
                            )
                            in_progress_comment.delete()
                            post_reply_comment(
                                usernames_length,
                                post,
                                errors_list,
                                called_list,
                                post_type,
                                url_link,
                                op,
                                dueling_sign_up_promo + dueling_info_text2,
                            )
                            print(
                                f"Posted reply to {post.id} by {op} in {str(post.subreddit)}."
                            )
                            # CREATE POST
                            post_title = "Answer Trivia for Points at r/Dueling"
                            post_text = (
                                "The home quiz just opened for this week's [r/Dueling](https://www.reddit.com/r/Dueling/) trivia game. Click on [**this link**]("
                                + quiz_url
                                + ') to start the quiz. The theme this week is **"'
                                + quiz_theme
                                + '!"** The quiz will be open until **'
                                + end_date
                                + "**"
                            )
                            print(post_title + "\n\n" + post_text)
                            r.subreddit("ravenclaw").submit(
                                title=post_title, selftext=post_text
                            )
                            print("Posted reminder post")
                        else:
                            print("Did not send dueling reminder")
                else:
                    print(f"Last post was less than {DATE_INTERVAL} days ago.")
                    print(
                        f"Last post: {get_date(last_post)} ({round(days_since_last_post, 4)} days ago)"
                    )
            elif "The Live Game is OVER!" in cbody:
                print(f"Top level: {top_level}")
                if not is_mod:
                    print(f"{post.author} is not in {mods}")
        else:
            print("Not a match.")


while True:
    global last_time
    subreddit = r.subreddit(SUBREDDIT)
    CHECK_INTERVAL = 10  # seconds to wait before checking again
    COMMENT_LIMIT = 30  # number of comments to check
    SUBMISSION_LIMIT = 10  # number of submissions to check
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
                    oauth_authenticate()
                    print("Gsheets authenticated")
                    print(f"Subreddit: {SUBREDDIT}")
                    print(
                        f"Checking last {COMMENT_LIMIT} comments and {SUBMISSION_LIMIT} submissions every {CHECK_INTERVAL} seconds..."
                    )
                    restart = False
                    break
            for comment in r.redditor(ME).comments.new(limit=1):
                last_time = get_date(comment)
            for comment in subreddit.comments(limit=COMMENT_LIMIT):
                process_post(comment, "comment")
            for submission in subreddit.new(limit=SUBMISSION_LIMIT):
                process_post(submission, "submission")
            time.sleep(CHECK_INTERVAL)
        except PrawcoreException as err:
            print(f"EXCEPTION: PrawcoreException. {err}")
            time.sleep(15)
            restart = True
        except Exception as err:
            print(f"EXCEPTION: An error occured. {err}")
            time.sleep(15)
            restart = True
