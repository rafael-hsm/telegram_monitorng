import config
import os
import json
import requests
from csv import DictWriter

import pandas as pd
from telethon import TelegramClient, events, sync
from telethon.tl.functions.channels import JoinChannelRequest
from telethon import functions, types
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)


class TelegramMonitor:
    """
    Class to start client telegram API using library telethon.
    Created functions to
    1 - Get a list of groups.
    2 - Join in groups
    3 - Monitoring Messages
    4 - Send message to slack.

    """

    def __init__(self):
        self.api_id = config.API_ID
        self.api_hash = config.API_HASH
        self.username = config.USERNAME
        self.phone = config.PHONE

        self.client = TelegramClient(self.username, self.api_id, self.api_hash)
        self.client.start()
        self.list_groups = []
        self.research_terms = []
        self.list_messages = []
        self.messages_to_send = []
        self.df = pd.DataFrame(columns=['date', 'title'])

    def research_groups(self):
        for i, v in enumerate(self.research_terms):
            result = self.client(functions.contacts.SearchRequest(
                q=v,
                limit=100
            ))
            result_dict = result.to_dict()
            result_list = result_dict['chats']
            for i, v in enumerate(result_list):
                try:
                    channel_id = v['id']
                    name = v['title']
                    username = v['username']
                    access_hash = v['access_hash']
                    participant_count = v['participants_count']
                    dict_groups = {'ID': channel_id, 'NAME': name, 'USERNAME': username, 'ACCESS_HASH': access_hash,
                                   'COUNT_PARTICIPANTS': participant_count}
                    with open('data_groups.csv', 'a', newline='\n') as file:
                        headersCSV = ['ID', 'NAME', 'USERNAME', 'ACCESS_HASH', 'COUNT_PARTICIPANTS']
                        dictwriter_object = DictWriter(file, fieldnames=headersCSV)
                        dictwriter_object.writerow(dict_groups)
                        file.close()
                    print(channel_id, name, participant_count)
                    self.list_groups.append(channel_id)
                except Exception as error:
                    print(error)
                    continue
        return self.list_groups

    def join_channel(self, group_id):
        """
        Use after start client to entry in some group. If group or channel don't have
        verification. It's possible but not implement
        :return:
        """
        join_group = self.client(JoinChannelRequest(group_id))
        # print(join_group)

    def get_message(self, group_id):
        for message in self.client.get_messages(group_id, limit=100):
            # print(message.stringify())
            # print(dir(message))
            self.list_messages.append(message.message)
            # self.df = pd.DataFrame(list_messages)

        # print(f"This is a list of messages: {list_messages}")
        # print(f"This is len: {len(list_messages)}")
        # print(self.df.head())
        # print(self.df.info())


def post_message_to_slack(text, blocks=None):
    return requests.post(
        "https://slack.com/api/chat.postMessage",
        {
            "token": config.TOKEN_SLACK,
            "channel": "#click-up-updates",
            "text": text,
            "icon_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTuGqps7ZafuzUsViFGIremEL2a3NR0KO0s0RTCMXmzmREJd5m4MA&s",
            "username": "Monitoring Bot",
            "blocks": json.dumps(blocks) if blocks else None,
            "link_names": True,
        },
    ).json()


if __name__ == '__main__':
    tm = TelegramMonitor()
    # Words to find groups.
    words_to_research = ['polygon', 'bitcoin', 'ethereum']

    for v in words_to_research:
        tm.research_terms.append(v)

    id_groups = tm.research_groups()

    # join in the groups
    for i, v in enumerate(id_groups):
        tm.join_channel(group_id=v)

    # monitoring message by word
    list_group_messages = []
    for i, v in enumerate(id_groups):
        # print(i, v)
        all_messages = tm.get_message(group_id=v)
        list_group_messages.append(all_messages)

    words_check = {'bad_words': ['SCAM', 'EXPLOIT', 'FRAUD', 'HACK', 'MALWARE', 'RUG PULL', 'PONZI',
                                 'PHISHING', 'HONEYPOT', 'UNLOCKED', 'THEFT', 'BLACKMAIL', ],
                   'god_words': ['AMUSING', 'AWESOME', 'FANTASTIC']}

    print(f"Total of messages: {len(tm.list_messages)}")
    count = 0
    while count < len(tm.list_messages):
        for i, v in words_check.items():
            if v == tm.list_messages[count].upper().split():
                message = tm.list_messages[count]
                tm.messages_to_send.append(message)

    print(tm.messages_to_send)

# print(tm.df.head())
# print(tm.df.info())

# print(id_groups)

#
# with client:
#     # https://t.me/coinsnipernet
#     client.loop.run_until_complete(info_groups(phone))
