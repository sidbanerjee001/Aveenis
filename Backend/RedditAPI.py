CLIENT_ID = '57wfqIvZxAc3yDoCqkIt4g'
SECRET = 'v9atZRxE6pKwXiUDQOIw74hCa9TG9g'

import requests
auth = requests.auth.HTTPBasicAuth(CLIENT_ID, SECRET)

with open('password.txt', 'r') as f:
    pw = f.read()

data = { 
       'grant_type' : 'password', 
       'username' : 'Entire-Award4624',
       'password' : pw
       }
headers = {'User-Agent' : 'MyAPI/0.0.1'}

res = requests.post('https://www.reddit.com/api/v1/access_token', 
                    auth=auth, data=data, headers=headers)
TOKEN = res.json()['access_token']
headers['Authorization'] = f'bearer {TOKEN}'

print(headers)

requests.get('https://oauth.reddit.com/api/v1/me', headers = headers).json()

oauth = 'https://oauth.reddit.com'

res = requests.get(f'{oauth}/r/chatgpt_promptDesign/hot', headers=headers)
res.json()


import pandas as pd
df = pd.DataFrame()
df_dict = {}
for post in res.json()['data']['children']:
    i = 0
    df_dict = pd.DataFrame(data={
                            'subreddit' : post['data']['subreddit'],
                            'title' : post['data']['subreddit'],
                            'selftext' : post['data']['selftext']
                           }, index=i)
    df = pd.concat([df, df_dict], axis=1, ignore_index=True)
    i+=1
df