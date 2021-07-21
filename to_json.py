from cab_1729 import playlist_id
from shelve import open as open_db
from json import dumps
video_data={}
with open_db(playlist_id,'r',writeback=False) as database:
    for k,v in database.items():#videos
        if len(k)==11:
            v['comments']={}
            video_data[k]=v;
    for k,v in database.items():#comments
        if '.' not in k and not k.startswith('https://') and len(k)!=11:
            vid_id=v['video']
            v['replies']={}
            v['url']=f'www.youtube.com/watch?v={vid_id}&lc={k}'
            video_data[vid_id]['comments'][k]=v
    for k,v in database.items():#replies
        if k.startswith('Ug') and '.' in k:
            ci=k[:k.index('.')]
            vid_id=database[ci]['video']
            v['url']=f'www.youtube.com/watch?v={vid_id}&lc={k}'
            video_data[vid_id]['comments'][ci]['replies'][k]=v
with open(playlist_id+'.json','w') as readable_database:
    readable_database.write(dumps(video_data,indent=4))
