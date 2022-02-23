from aiosseclient import aiosseclient
import asyncio
import json

# Set time and domain to monitor user changes
print_after = 60
domain_check = 'en.wikipedia.org'

wiki_list = []
domain_list= []

async def get_wiki():
    async for event in aiosseclient('https://stream.wikimedia.org/v2/stream/revision-create'):
        if event.event == 'message':
            try:
                change = json.loads(event.data)
            except ValueError:
                pass
            else:
                domain = change['meta']['domain']
                username = change['performer']['user_text']
                user_is_bot = change['performer']['user_is_bot']
                try:
                    user_edit_count = change['performer']['user_edit_count']
                except:
                    # If user_edit_count not available/anonymous edit
                    user_edit_count = 1
                user_details = {'username':username, 'user_is_bot':user_is_bot, 'user_edit_count':user_edit_count}

                if not len(wiki_list) or domain not in domain_list:
                    wiki_list.append({'domain':domain, 'count':1, 'user_details':[user_details]})
                    domain_list.append(domain)

                # If domian data exists in list; add count and user details
                else:
                    for data in wiki_list:
                        if domain == data['domain']:
                            data['count'] += 1
                            for user in data['user_details']:
                                if user['username'] == user_details['username']:
                                    data['user_details'].remove(user)
                            data['user_details'].append(user_details)


async def print_wiki():
    global wiki_list, domain_list
    while True:
        await asyncio.sleep(print_after)
        print('\n+++++++++++\n')

        # Printing domain updates
        lines = sorted(wiki_list, key=lambda k: k['count'], reverse=True)
        print('Total number of Wikipedia Domains Updated: {}\n'.format(len(lines)))
        for line in lines:
            print('{} : {} pages updated'.format(line['domain'], line['count']))

        # Sorting users based on total edits
        sorted_users = []
        for data in wiki_list:
            if data['domain'] == domain_check:
                sorted_users = sorted(data['user_details'], key=lambda k: k['user_edit_count'], reverse=True)

        # Printing user updates in domain set
        print('\nUsers who made changes to en.wikipedia.org\n')
        for user in sorted_users:
            if not user['user_is_bot']:
                print('{} : {}'.format(user['username'], user['user_edit_count']))

        wiki_list = []
        domain_list= []


async def main():
    # Running functions concurrently
    await asyncio.gather(get_wiki(),print_wiki())

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()

