# Origin-Write-Genres
### A python script that loops through a directory, opens the origin file and maps tags to genres and styles and writes them to the vorbis GENRE and STYLE comments.

It uses a small standard set of genres but allows anything for styles.  It first checks a release and if the tags include a genre it assigns it and if not it uses the associated mapping csv file to assign a genre(s) based on the the existing tags.
It can assign more than one genre and more than one style. When it writes the vorbis comments it uses ; to seperate values in comment.
It uses the release type of soundtrack to assign soundtrack as a genre.  It will also log any albums that it can't assign a genre to or are missing genre tags altogeher.

This project has a dependency on the gazelle-origin project created by x1ppy. gazelle-origin scrapes gazelle based sites and stores the related music metadata in a yaml file in the music albums folder. For this script to work you need to use a fork that has additional metadata including the cover art. The fork that has the most additional metadata right now is: https://github.com/spinfast319/gazelle-origin

This has only been tested to work with flac files and would need to be modified to work with mp3 or other types of music files. The script can handle albums with artwork folders or multiple disc folders in them. It can also handle specials characters. It has been tested and works in both Ubuntu Linux and Windows 10.

## Install and set up
1) Clone this script where you want to run it.

2) Install [mutagen](https://pypi.org/project/mutagen/) with pip. (_note: on some systems it might be pip3_) 

to install it:

```
pip install mutagen
```

3) Install [ruamel yaml](https://pypi.org/project/ruamel.yaml/) with pip. (_note: on some systems it might be pip3_) 

to install it:

```
pip install ruamel.yaml
```

4) Edit the script where it says _Set your directories here_ to set up or specify the three directories you will be using. Write them as absolute paths for:

    A. The directory where the albums you want to write genre and style tags to  
    B. The directory to store the log files the script creates  
    C. The directory where albums which have no genre tag will be moved for manual fixing 

5) Edit the script where it says _Set whether you are using nested folders_ to specify whether you are using nested folders or have all albums in one directory 

    A. If you have all your ablums in one music directory, ie. Music/Album then set this value to 1 (the default)  
    B. If you have all your albums nest in a Music/Artist/Album style of pattern set this value to 2

6) Edit the script where it says _Set whether you want to move folders that have missing final genre tags_ to specify whether you want to have ths script move albums missing genre tags to a different directory

    A. If you want the script to move albums then set this value to True (the default)
    B. If you do not want the albums to be moved set this value to False (they will still be logged)

7) Use your terminal to navigate to the directory the script is in and run the script from the command line.  When it finishes it will output how many albums it wrote tags to.

```
Origin-Write-Tags.py
```

_note: on linux and mac you will likely need to type "python3 Origin-Write-Tags.py"_  
_note 2: you can run the script from anywhere if you provide the full path to it_

The script will also create logs listing any album that is missing genre tags in both the origin files and flac files.  


