# Origin-Write-Genres
### A python script that loops through a directory, opens the origin file and maps tags to genres and styles and writes them to the vorbis GENRE and STYLE comments.

It uses a small standard set of genres but allows anything for styles.  It first checks a release and if the tags include a genre it assigns it and if not it uses the associated mapping csv file to assign a genre(s) based on the the existing tags.
It can assign more than one genre and more than one style. When it writes the vorbis comments it uses ; to seperate values in comment.
It uses the release type of soundtrack to assign soundtrack as a genre.  It will also log any albums that it can't assign a genre to or are missing genre tags altogeher.
This has only been tested to work with flac files.
It can handle albums with artwork folders or multiple disc folders in them. It can also handle specials characters.
It has been tested and works in both Ubuntu Linux and Windows 10.
