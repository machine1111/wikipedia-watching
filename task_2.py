from aiosseclient import aiosseclient
import asyncio
import json


# Set time and domain to monitor user changes
print_after = 60
domain_check = 'en.wikipedia.org'

wiki_time_list = []
wiki_list = []
domain_list= []
timer = 1

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
                    user_edit_count = 1
                user_details = {'username':username, 'user_is_bot':user_is_bot, 'user_edit_count':user_edit_count}

                if not len(wiki_list) or domain not in domain_list:
                    wiki_list.append({'domain':domain, 'count':1, 'user_details':[user_details]})
                    domain_list.append(domain)
                else:
                    for data in wiki_list:
                        if domain == data['domain']:
                            data['count'] += 1
                            for user in data['user_details']:
                                if user['username'] == user_details['username']:
                                    data['user_details'].remove(user)
                            data['user_details'].append(user_details)


async def print_wiki():
    global wiki_time_list, wiki_list, domain_list, timer
    while True:
        await asyncio.sleep(print_after)
        
        wiki_time_list.append(wiki_list)
        # Every 5 minutes first minute data removed
        if len(wiki_time_list) > 5:
            del wiki_time_list[0]

        print('\nMinute {} Report -\n'.format(timer))

        all_data = []

        for wiki in wiki_time_list:
            for i in wiki:
                if len(all_data) == 0 or i['domain'] not in [data['domain'] for data in all_data]:
                    all_data.append(i)
                else:
                    for data in all_data:
                        if data['domain'] == i['domain']:
                            data['count'] += i['count']
                            
                            # Remove same user edit for same domain
                            all_user_details = data['user_details'] + i['user_details']
                            sorted_users = sorted(all_user_details, key=lambda k: k['user_edit_count'], reverse=True)
                            all_ids = [each['username'] for each in sorted_users]
                            user_details_cleaned = [sorted_users[all_ids.index(id)] for id in set(all_ids)]

                            data['user_details'] = user_details_cleaned


        lines = sorted(all_data, key=lambda k: k['count'], reverse=True)
        print('Total number of Wikipedia Domains Updated: {}\n'.format(len(lines)))
        for line in lines:
            print('{} : {} pages updated'.format(line['domain'], line['count']))

        sorted_users = []
        for data in all_data:
            if data['domain'] == domain_check:
                sorted_users = sorted(data['user_details'], key=lambda k: k['user_edit_count'], reverse=True)
        print('\nUsers who made changes to en.wikipedia.org\n')
        for user in sorted_users:
            if not user['user_is_bot']:
                print('{} : {}'.format(user['username'], user['user_edit_count']))

        wiki_list = []
        domain_list= []
        timer += 1


async def main():
    await asyncio.gather(get_wiki(),print_wiki())

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()

