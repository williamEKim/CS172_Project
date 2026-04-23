import praw
from getpass import getpass

client_id = client_secrete = user_agent = ''
username = pw = ''

client_id = input('Please Enter Your Reddit Client ID: ')
client_secrete = input('Please Enter Your Reddit Client Secrete: ')
user_agent = input('Please Enter Your Reddit User Agent: ')

username = input('Please Enter your Reddit Username: ')
pw = getpass('Please Enter your Reddit user password: ')


reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secrete,
    user_agent=user_agent,
    username=username,
    password=pw
)

print('\nRead Only Access is Successfully Granted!\n\t' + reddit.read_only)

subreddit = input('Enter the subreddit you want to crawl: ')

# obtain 10 “hot” submissions from r/'your input'
for submission in reddit.subreddit(subreddit).hot(limit=10):
    print(submission.title)

# Output: 10 submissions