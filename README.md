# Tag-Owl-Reddit-Bot

Reddit bot to tag long lists of users.

This bot sends notifications to users when:

* A new post is created in a subreddit (for [r/ravenclaw](https://www.reddit.com/r/ravenclaw), [r/RavenclawsBookClub](https://www.reddit.com/r/RavenclawsBookClub), [r/Arithmancy](https://www.reddit.com/r/Arithmancy))
* Someone writes "send by owl" in a comment (eg. "Send by owl to Assignments List", "Send by owl to u/example1, u/example2")
* A comment is posted mentioning a link to a Home Game (for [r/Dueling](https://www.reddit.com/r/Dueling))

Info on getting Reddit client id, client secret for bot account: https://progur.com/2016/09/how-to-create-reddit-bot-using-praw4.html

Steps for setting up Google Sheets API and `creds.json` with Google credentials: https://erikrood.com/Posts/py_gsheets.html

I'm currently running the script using Heroku - https://dashboard.heroku.com/apps

> **Note**
> I know the code is a mess, this is an old project that I'm not actively working on.
