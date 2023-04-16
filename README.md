# Origin-Write-Genres
### A python script that loops through a directory, opens the origin file and maps tags to genres and styles and writes them to the vorbis GENRE and STYLE comments.

Getting consistent genre tags in a music collection is challenging.  If your music comes from a place that has a consistent metadata tagging schema you might prefer to add those tags to your music rather than try to manually add genre tags, derive them from artists or use beets or picard to pull from public repositories like discogs or musicbrainz. This script allows you use the tags provided from the source where you attain your music as your genre tags.  It is meant to work in tandem with the [Origin Combine Genres](https://github.com/spinfast319/Origin-Combine-Genres) script which merges and standardizes the genre, mood and style vorbis comments and the tags from the origin site and stores them all in the origin file.

This script goes a step further and automatically sorts the tags into genres and styles using a custom taxomony that is based closely on discogs taxonomy. If you have coding skills you could customize this to your own particular interests.  It uses a small tightly defined standard set of genres but allows anything for styles.  It first checks a release and if the tags include a genre it assigns it and if not it uses the associated mapping csv file to assign a genre(s) based on the the existing tags. 

An example of this would be an album with the tag deep.house.  The script would use the genre map to add the tags electronic and house to that album. It would then write Electronic to the vorbis GENRE comment in the flac and write Deep House; House to the vorbis STYLE comment in the flac overwriting whatever what there previously.

The mapping is quite extensive but if a genre either doesn't exist or can't be derived from the existing tags it will log that album and move it to a folder to be dealt with manually. 

An example of this would be an album only tagged with the tag experimental.  It would first log that album as not having a clear genre and then move the album to a folder you specify so you can determin whether it is experimental rock, electronic music, jazz or something else.

It can assign more than one genre and more than one style. When it writes the vorbis comments it uses ; to seperate values in the comments which is the standard for the MusicBee software but that could easily be altered as well.  It writes the comments as seperate words that capitalized. 

It does a number of other things that are likely particular to my personal taxonmy.  You could comment well documented lines out in the main function to not execute those functions or add additional functions to further customize it. These things include:
- It uses the release type of soundtrack to assign soundtrack as a genre.  
- It removes decade tags if the album was released in that decade but keeps them if it wasn't. (ie. a compilation of music from the 1960s that was released in 2004 and had tags for both 1960s and 2000s would have the 2000s tag removed but keep the 1960s tag)
- It removes a set of tags that are not relevant for music discovery (i.e. freely.available)
- It reserves the use of the pop tag for commercial radio style pop and removes it if it finds tags like indie, indie.pop etc.
- It will only add the non.music tag as a genere if there is not another genre.  (ie. a rock album with spoken.word as a tag will not get the Non Music genre added but an album with only that tag will get assigned a genre tag of Non Music and a style tag of Spoken Word.) 

After it has sorted the tags into genre's and styles and written them to the flac files, it will write the full set of tags to origin file so the metadata is consistent between the tags and origin file.  It writes those tags in format of the origin site (eg. all lower case with dots seperating words).

After your music has been updated in your player of choice you can configure it to display the genre's and styles (in apps like MusicBee and Foobar2000) and it is recommended that you double check the tags to see if they are what you want. I estimate that I tweak about 1 in 25 albums that the scripts tags for me.

This project has a dependency on the gazelle-origin project created by x1ppy. gazelle-origin scrapes gazelle based sites and stores the related music metadata in a yaml file in the music albums folder. For this script to work you need to use a fork that has additional metadata including the cover art. The fork that has the most additional metadata right now is: https://github.com/spinfast319/gazelle-origin  You need your entire music collectin to already have origin files based on this fork for it to work.

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


