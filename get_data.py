#imports
from shelve import open
from colorama import Fore,Back,init
from asyncio import run,create_task,gather,sleep
from aiohttp import ClientSession
from cab_1729 import api_key,playlist_id,need_data
#globals
    #semaphores, tinker and adjust
    #increase if better bandwidth to get more speed
video_coroutines=10
comment_coroutines=30
reply_coroutines=10
picture_coroutines=20#no api, data heavy
    #global resources
dump=open(playlist_id)
pictures_obtained=set()
completed_video_ids=[]
incomplete_video_ids=[]
quota_exhausted=False
state=open('state',writeback=True)
    #colors
init(convert=True)
getting_videos=Fore.LIGHTYELLOW_EX
getting_comments=Fore.LIGHTGREEN_EX
got_comments=Back.GREEN+Fore.WHITE
getting_replies=Fore.LIGHTBLUE_EX
got_replies=Back.BLUE+Fore.WHITE
getting_picture=Fore.LIGHTCYAN_EX
got_picture=Back.CYAN+Fore.WHITE
back2black=Back.BLACK
special_message=Fore.LIGHTRED_EX
#functions
async def store(shelve_name,key,data):
    while True:#keep trying
        try:
            shelve_name[key]=data
            break#successful, stop trying
        except PermissionError:
            print(f'{special_message}Permission Error, waiting and retrying')
            await sleep(2.0)
async def get_picture(connection,url,picture_of,dont_check):
    if dont_check or url not in pictures_obtained:
        global picture_coroutines
        pictures_obtained.add(url)
        while picture_coroutines==0:await sleep(3.0)
        print(f'{getting_picture}Getting {picture_of} ...')
        picture_coroutines-=1#lock
        async with connection.get(url) as resp:await store(dump,url,await resp.read())
        print(f'{got_picture}Got {picture_of}{back2black}')
        picture_coroutines+=1#release
#coroutines
async def comment(comment_id,video_id,comment_text,author_name,author_id,author_profile_image,likes,commented_at,reply_count,nT):#goes through replies
    def die():
        global comment_coroutines
        comment_coroutines+=1#release
        state[video_id].append((comment_id,video_id,comment_text,author_name,author_id,author_profile_image,likes,commented_at,reply_count,nT))
        return False
    global comment_coroutines,reply_coroutines,quota_exhausted
    need_comment=False
    async with ClientSession() as internet:
        if reply_count!=0:
            req=f'https://youtube.googleapis.com/youtube/v3/comments?part=snippet&maxResults=100&parentId={comment_id}&textFormat=plainText&key={api_key}&pageToken='
            beg=f'{getting_replies}Getting some replies of {comment_id} ...';end=f'{getting_replies}Got some replies of {comment_id}'
            while True:#replies request
                if quota_exhausted:
                    return die()
                print(beg)
                async with internet.get(req+nT) as resp:
                    if resp.status==403:
                        quota_exhausted=True
                        print(f'{special_message}\nQuota exhausted\nSaving state and quiting\n')
                        return die()
                    data=await resp.json()
                    for reply_data in data['items']:
                        while reply_coroutines==0:await sleep(4.0)#wait if too many
                        reply_coroutines-=1#lock
                        snippet=reply_data['snippet']
                        reply_text=snippet['textDisplay']
                        if need_data(reply_text):
                            need_comment=True
                            reply_author_image=snippet['authorProfileImageUrl']
                            channel=snippet['authorChannelUrl'][31:]
                            await get_picture(internet,reply_author_image,f'profile picture of {channel}',False)
                            await store(dump,reply_data['id'],{
                                    'reply text':reply_text,
                                    'author id':channel,
                                    'author name':snippet['authorDisplayName'],
                                    'author profile image':reply_author_image,
                                    'likes':snippet['likeCount'],
                                    'replied at':snippet['updatedAt']
                            })
                        reply_coroutines+=1#release
                print(end)
                try:nT=data['nextPageToken']#go to next page
                except KeyError:
                    print(f'{got_replies}Got all replies of {comment_id}{back2black}')
                    break#no more replies
        if need_comment or need_data(comment_text):
            await get_picture(internet,author_profile_image,f'profile picture of {author_id}',False)
            await store(dump,comment_id,{
                    'comment text':comment_text,
                    'video':video_id,
                    'author id':author_id,
                    'author name':author_name,
                    'author profile image':author_profile_image,
                    'likes':likes,
                    'reply count':reply_count,
                    'commented at':commented_at
            })
            comment_coroutines+=1#release
            return True
    comment_coroutines+=1#release
async def video(video_id,video_title,released_at,nT,not_saved,coroutines):#goes through comments
    async def die():
        need_video=True in await gather(*coroutines)
        if need_video and not_saved:
            await get_picture(internet,f'https://i.ytimg.com/vi/{video_id}/sddefault.jpg',f'thumbnail of {video_id}',True)
            await store(dump,video_id,{'title':video_title,'publish time':released_at})
        global video_coroutines
        video_coroutines+=1#release
        incomplete_video_ids.append((video_id,video_title,released_at,nT,not need_video))
    global comment_coroutines,video_coroutines,quota_exhausted
    await store(state,video_id,[])
    async with ClientSession() as internet:
        req=f'https://youtube.googleapis.com/youtube/v3/commentThreads?part=snippet&maxResults=100&videoId={video_id}&textFormat=plainText&order=relevance&key={api_key}&pageToken='
        beg=f'{getting_comments}Getting some comments of {video_id} ...';end=f'{getting_comments}Got some comments of {video_id}'
        while True:#comments request
            if quota_exhausted:
                return await die()
            print(beg)
            async with internet.get(req+nT) as resp:
                data=await resp.json()#parsing before because 2 errors give 403
                if resp.status==403:
                    reason=data['error']['errors'][0]['domain']
                    if reason=='youtube.quota':#quota_exhausted
                        quota_exhausted=True
                        print(f'{special_message}\nQuota exhausted\nSaving state and quiting\n')
                        return await die()
                    elif reason=='youtube.commentThread':#comments disabled for video
                        print(f'{special_message}Comments not available for {video_id}')
                        del state[video_id]
                        return
                for comment_data in data['items']:
                    while comment_coroutines==0:await sleep(2.0)#wait if too many
                    comment_coroutines-=1#lock
                    usnippet=comment_data['snippet']
                    topLevelComment=usnippet['topLevelComment']
                    snippet=topLevelComment['snippet']
                    coroutines.append(create_task(comment(
                        topLevelComment['id'],
                        video_id,
                        snippet['textDisplay'],
                        snippet['authorDisplayName'],
                        snippet['authorChannelUrl'][31:],
                        snippet['authorProfileImageUrl'],
                        snippet['likeCount'],
                        snippet['updatedAt'],
                        usnippet['totalReplyCount'],
                        ''
                    )))
            print(end)
            try:nT=data['nextPageToken']#go to next page
            except KeyError:
                print(f'{got_comments}Got all comments of {video_id}{back2black}')
                break#no more comments
        results=await gather(*coroutines)
        need_video=True in results
        if False in results:#if not all comments gone through
            completed_video_ids.append((video_id,video_title,released_at,not need_video))
            if need_video and not_saved:
                await get_picture(internet,f'https://i.ytimg.com/vi/{video_id}/sddefault.jpg',f'thumbnail of {video_id}',True)
                await store(dump,video_id,{'title':video_title,'publish time':released_at})
        elif need_video and not_saved:#if all comments gone through and video needed
            await get_picture(internet,f'https://i.ytimg.com/vi/{video_id}/sddefault.jpg',f'thumbnail of {video_id}',True)
            del state[video_id]#remove list from file
            await store(dump,video_id,{'title':video_title,'publish time':released_at})
        else:#if not needed
            del state[video_id]#remove list from file
    video_coroutines+=1#release
async def video_complete(video_id,video_title,released_at,not_saved):#collects rest of comments
    global comment_coroutines
    coroutines=[]
    for args in state[video_id]:
        comment_coroutines-=1#lock
        coroutines.append(create_task(comment(*args)))
    results=await gather(*coroutines)
    async with ClientSession() as internet:
        if False in results:#if not determined:
            completed_video_ids.append((video_id,video_title,released_at))
        if True in results and not_saved:#if video needed
            await get_picture(internet,f'https://i.ytimg.com/vi/{video_id}/sddefault.jpg',f'thumbnail of {video_id}',True)
            await store(dump,video_id,{'title':video_title,'publish time':released_at})
async def playlist(nT):#goes through videos
    async def die():
        await gather(*coroutines)
        await store(state,playlist_id,nT)
    global video_coroutines,quota_exhausted
    req=f'https://youtube.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={playlist_id}&key={api_key}&pageToken='
    beg=f'{getting_videos}Getting some videos of {playlist_id} ...';end=f'{getting_videos}Got some videos of {playlist_id}'
    coroutines=[]
    async with ClientSession() as internet:
        while True:#vids request
            if quota_exhausted:
                return await die()
            print(beg)
            async with internet.get(req+nT) as resp:
                if resp.status==403:
                    quota_exhausted=True
                    print(f'{special_message}\nQuota exhausted\nSaving state and quiting\n')
                    return await die()
                data=await resp.json()
                for video_data in data['items']:
                    snippet=video_data['snippet']
                    while video_coroutines==0:await sleep(5.0)#wait if too many
                    video_coroutines-=1#lock
                    coroutines.append(create_task(video(
                        snippet['resourceId']['videoId'],
                        snippet['title'],
                        snippet['publishedAt'],
                        '',True,[]
                    )))
            print(end)
            try:nT=data['nextPageToken']#go to next page
            except KeyError:
                print(Fore.WHITE+Back.YELLOW+f'Got all videos of {playlist_id}{back2black}')
                break#no more videos
    await gather(*coroutines)
async def main():
    playlist_token=''
    if state:#if previous state exists, continue from previous
        global video_coroutines,pictures_obtained
        pictures_obtained=state['pictures'].copy()
        coroutines=[]
        for i in state['completed video ids']:
            coroutines.append(create_task(video_complete(*i)))
        for i in state['incomplete video ids']:
            video_coroutines-=1#lock
            coroutines.append(create_task(video(
                *i,
                [create_task(comment(*args))
                    for args in state[i[0]]
                ]
            )))
        await gather(*coroutines)
        playlist_token=state[playlist_id]
        state.clear()
    await store(state,'completed video ids',completed_video_ids)
    await store(state,'incomplete video ids',incomplete_video_ids)
    await store(state,'pictures',pictures_obtained)
    await playlist(playlist_token)
    if not quota_exhausted:
        print(f'{special_message}Done\n\nGot all data')
    #saving data
    dump.close()
    state.close()
if __name__=='__main__':
    run(main())
