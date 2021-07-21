#keep your tests here
#these are mine
from shelve import open as open_db
from cab_1729 import playlist_id
vid_ids=set();vc=set()
with open_db(playlist_id,'r') as data:
    for i in data.keys():
        if i.startswith('Ug') and '.' not in i:
            try:
                data[data[i]['video']]
            except KeyError:
                print(i,data[i]['video'])
with open_db('state','r') as state:
    print(f"state['completed video ids'] = {state['completed video ids']}")
    vid_ids={i for i in state.keys() if len(i)==11}
    vid={i[0] for i in state['incomplete video ids']}.union({i[0] for i in state['completed video ids']})
    print(f'vid_ids-vid = {vid_ids-vid}');print(f'vid-vid_ids = {vid-vid_ids}')
    print('Videos with blank data : ')
    for i in vid_ids:
        if state[i]==[]:
            print(i)
