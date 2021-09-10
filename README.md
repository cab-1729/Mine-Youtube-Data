# Mine-Youtube-Data
Code that mines data from the youtube comments section from any playlist.

##### A Data Mining Script
![gif that is absolutely unnecessary](https://github.com/cab-1729/Mine-Youtube-Data/blob/main/GIF.gif)

### Note : This is not an application or a module to be downloaded and used. It is more like a blueprint to use for mining data. I created this for my use only, but it is public to view and anyone can use it if they can figure out how to.

+ This uses the Youtube Data Api. Data must be collected over the course of days, since the youtube data api has a daily quota. _get_data.py_ is to be run each day with renewed quota until all data has been collected. The key given will be used to exhaustion on any particular day
+ For reference, _quota exhausted.json_ contains the response given by youtube when the quota has been used and _comments disabled.json_ contains the response given by youtube when the comments for a video are disabled.
+ _get_data.py_ does the actual data mining, _cab_1729.py_ contains all details for what to mine.
+ _to_json.py_ converts the data to a more human readable format. **It does not however convert all the data, images are also stored.**
+ Data is stored in shelve files with the same name as the playlist, _state_ shelf stores how much data has been mined, for next time.
+ It is recommended to not change anything in the files before all the data has been mined, except the semaphore counts given in _get_data.py_
+ _logs_ directory is for storing the output log which is not done by default. I personally use [tmux-logging](https://github.com/tmux-plugins/tmux-logging) for that.
+ _storage_ is a folder to backup the data
+ .bat files are for quickly handling backup
+ _tests.py_ is for storing the tests.
+ In order to use, it is almost necessary to read the code or open the data shelf using python to understand in what format the data is being stored.
+ All the filtering is done natively, so filtering code is completely private. This goes through all the available comments from the playlist, so Youtube servers only get the API key, IP, and playlist id.
