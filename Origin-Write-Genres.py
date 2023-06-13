#!/usr/bin/env python3

# Write Genres
# author: hypermodified
# This python script loops through a directory, opens the origin file and maps tags to genres and styles and writes them to the vorbis GENRE and STYLE comments.
# It uses a small standard set of genres but allows anything for styles.  It first checks a release and if the tags include a genre it assigns it and if not it uses the associated mapping csv file to assign a genre(s) based on the the existing tags.
# It can assign more than one genre and more than one style. When it writes the vorbis comments it uses ; to seperate values in comment.
# It uses the release type of soundtrack to assign soundtrack as a genre.  It will also log any albums that it can't assign a genre to or are missing genre tags altogeher.
# This has only been tested to work with flac files.
# It can handle albums with artwork folders or multiple disc folders in them. It can also handle specials characters.
# It has been tested and works in both Ubuntu Linux and Windows 10.

# Before running this script install the dependencies
# pip install mutagen
# pip install ruamel.yaml

# Import dependencies
import os  # Imports functionality that let's you interact with your operating system
import ruamel.yaml  # Imports the ruamel fork of yaml
import shutil  # Imports functionality that lets you copy files and directory
import datetime  # Imports functionality that lets you make timestamps
import mutagen  # Imports functionality to get metadata from music files
import csv  # Imports functionality to parse CSV files
import re  # Imports functionality to use regular expressions
import string  #  Imports functionality to manipulate strings
import hashlib  # Imports the ability to make a hash
import pickle  # Imports the ability to turn python objects into bytes

import origin_script_library as osl  # Imports common code used across all origin scripts

#  Set the location of the local directory
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


#  Set your directories here
album_directory = "M:\PROCESS"  # Which directory do you want to start with?
log_directory = "M:\PROCESS-LOGS\Logs"  # Which directory do you want the log in?
sort_directory = "M:\PROCESS-SORT\Missing Genre"  # Directory to move albums missing genres to so you can manually fix them

# Set whether you are using nested folders or have all albums in one directory here
# If you have all your ablums in one music directory Music/Album_name then set this value to 1
# If you have all your albums nest in a Music/Artist/Album style of pattern set this value to 2
# The default is 1
album_depth = 2

# Set whether you want to move folders that have missing final genre tags to a folder so they can be dealt with manually later# creates the list of albums that need to be moved post sorting
# If you want to move your albums set move_flag to True
# If you do NOT want to move your albums set move_flag to False
# The folders will be logged either way so you can always see which albums were missing final genre tags.
move_flag = True
move_list = []


# Establishes the counters for completed albums and missing origin files
count = 0
total_count = 0
error_message = 0
good_missing = 0
bad_missing = 0
parse_error = 0
origin_old = 0
missing_genre_origin = 0
missing_genre = 0
missing_tags = 0
track_count = 0
missing_final_genre = 0
move_count = 0
flac_folder_count = 0

# identifies album directory level
path_segments = album_directory.split(os.sep)
segments = len(path_segments)
album_location_check = segments + album_depth


# A function to log events
def log_outcomes(directory, log_name, message, log_list):
    global log_directory

    script_name = "Write Genres Script"
    today = datetime.datetime.now()
    log_name = f"{log_name}.txt"
    album_name = directory.split(os.sep)
    album_name = album_name[-1]
    log_path = os.path.join(log_directory, log_name)
    with open(log_path, "a", encoding="utf-8") as log_name:
        log_name.write(f"--{today:%b, %d %Y} at {today:%H:%M:%S} from the {script_name}.\n")
        log_name.write(f"The album folder {album_name} {message}.\n")
        if log_list != None:
            log_name.write("\n".join(map(str, log_list)))
            log_name.write("\n")
        log_name.write(f"Album location: {directory}\n")
        log_name.write(" \n")
        log_name.close()


# A function that determines if there is an error
def error_exists(error_type):
    global error_message

    if error_type >= 1:
        error_message += 1  # variable will increment if statement is true
        return "Warning"
    else:
        return "Info"


# A function that writes a summary of what the script did at the end of the process
def summary_text():
    global count
    global total_count
    global error_message
    global parse_error
    global bad_missing
    global good_missing
    global origin_old
    global missing_genre_origin
    global track_count
    global missing_final_genre
    global move_count
    global flac_folder_count

    print("")
    print(f"This script wrote tags for {track_count} tracks in {count} folders out of {flac_folder_count} folders for {total_count} albums.")
    if move_count != []:
        print(f"The script moved {move_count} albums that were missing final genres so you can fix them manually.")
    print("This script looks for potential missing files or errors. The following messages outline whether any were found.")

    error_status = error_exists(parse_error)
    print(f"--{error_status}: There were {parse_error} albums skipped due to not being able to open the yaml. Redownload the yaml file.")
    error_status = error_exists(origin_old)
    print(f"--{error_status}: There were {origin_old} origin files that do not have the needed metadata and need to be updated.")
    error_status = error_exists(bad_missing)
    print(f"--{error_status}: There were {bad_missing} folders missing an origin files that should have had them.")
    error_status = error_exists(missing_genre_origin)
    print(f"--{error_status}: There were {missing_genre_origin} folders missing genre tags in their origin files.")
    error_status = error_exists(missing_final_genre)
    print(f"--{error_status}: There were {missing_final_genre} albums where a genere tag could not be mapped and was missing. Fix these manually.")
    error_status = error_exists(good_missing)
    print(f"--Info: Some folders didn't have origin files and probably shouldn't have origin files. {good_missing} of these folders were identified.")

    if error_message >= 1:
        print("Check the logs to see which folders had errors and what they were and which tracks had metadata written to them.")
    else:
        print("There were no errors.")


# A function to check whether the directory is a an album or a sub-directory and returns an origin file location and album name
def level_check(directory):
    global total_count
    global album_location_check
    global album_directory

    print(f"--Directory: {directory}")
    print(f"--The albums are stored {album_location_check} folders deep.")

    path_segments = directory.split(os.sep)
    directory_location = len(path_segments)

    print(f"--This folder is {directory_location} folders deep.")

    # Checks to see if a folder is an album or subdirectory by looking at how many segments are in a path and returns origin location and album name
    if album_location_check == directory_location and album_depth == 1:
        print("--This is an album.")
        origin_location = os.path.join(directory, "origin.yaml")
        album_name = path_segments[-1]
        total_count += 1  # variable will increment every loop iteration
        return origin_location, album_name
    elif album_location_check == directory_location and album_depth == 2:
        print("--This is an album.")
        origin_location = os.path.join(directory, "origin.yaml")
        album_name = os.path.join(path_segments[-2], path_segments[-1])
        total_count += 1  # variable will increment every loop iteration
        return origin_location, album_name
    elif album_location_check < directory_location and album_depth == 1:
        print("--This is a sub-directory")
        origin_location = os.path.join(album_directory, path_segments[-2], "origin.yaml")
        album_name = os.path.join(path_segments[-2], path_segments[-1])
        return origin_location, album_name
    elif album_location_check < directory_location and album_depth == 2:
        print("--This is a sub-directory")
        origin_location = os.path.join(album_directory, path_segments[-3], path_segments[-2], "origin.yaml")
        album_name = os.path.join(path_segments[-3], path_segments[-2], path_segments[-1])
        return origin_location, album_name
    elif album_location_check > directory_location and album_depth == 2:
        print("--This is an artist folder.")
        origin_location = None
        album_name = None
        return origin_location, album_name


# A function to check whether a directory has flac and should be checked further
def flac_check(directory):
    global flac_folder_count

    # Loop through the directory and see if any file is a flac
    for fname in os.listdir(directory):
        if fname.lower().endswith(".flac"):
            print("--There are flac in this directory.")
            flac_folder_count += 1  # variable will increment every loop iteration
            return True

    print("--There are no flac in this directory.")
    return False


# A function to check if the origin file is there and to determine whether it is supposed to be there.
def check_file(directory):
    global good_missing
    global bad_missing
    global album_location_check

    # check to see if there is an origin file
    file_exists = os.path.exists("origin.yaml")
    # if origin file exists, load it, copy, and rename
    if file_exists == True:
        return True
    else:
        # split the directory to make sure that it distinguishes between folders that should and shouldn't have origin files
        current_path_segments = directory.split(os.sep)
        current_segments = len(current_path_segments)
        # create different log files depending on whether the origin file is missing somewhere it shouldn't be
        if album_location_check != current_segments:
            # log the missing origin file folders that are likely supposed to be missing
            print("--An origin file is missing from a folder that should not have one.")
            print("--Logged missing origin file.")
            log_name = "good-missing-origin"
            log_message = "origin file is missing from a folder that should not have one.\nSince it shouldn't be there it is probably fine but you can double check"
            log_list = None
            log_outcomes(directory, log_name, log_message, log_list)
            good_missing += 1  # variable will increment every loop iteration
            return False
        else:
            # log the missing origin file folders that are not likely supposed to be missing
            print("--An origin file is missing from a folder that should have one.")
            print("--Logged missing origin file.")
            log_name = "bad-missing-origin"
            log_message = "origin file is missing from a folder that should have one"
            log_list = None
            log_outcomes(directory, log_name, log_message, log_list)
            bad_missing += 1  # variable will increment every loop iteration
            return False


# This function changes the emitter in the yaml dump to use ~ rather than null or blank
def _represent_none(self, data):
    if len(self.represented_objects) == 0 and not self.serializer.use_explicit_start:
        return self.represent_scalar("tag:yaml.org,2002:null", "null")
    return self.represent_scalar("tag:yaml.org,2002:null", "~")


#  A function that gets the directory and then opens the origin file and extracts the needed variables
def get_genre_origin(directory, origin_location, album_name):
    global parse_error
    global origin_old
    global bad_missing
    global missing_genre_origin

    print(f"--Getting metadata for {album_name}")
    print(f"--From: {origin_location}")

    # check to see if there is an origin file is supposed to be in this specific directory
    file_exists = check_file(directory)
    # check to see the origin file location variable exists
    location_exists = os.path.exists(origin_location)
    # set up variables that will be pulled from origin file to avoid None type errors
    genre_origin = []
    original_date = None
    release_type = None

    if location_exists == True:
        print("--The origin file location is valid.")
        # open the yaml
        try:
            yaml = ruamel.yaml.YAML()
            yaml.preserve_quotes = True
            yaml.allow_unicode = True
            yaml.encoding = "utf-8"
            yaml.width = 4096
            with open(origin_location, encoding="utf-8") as f:
                data = yaml.load(f)

        except:
            print("--There was an issue parsing the yaml file and the metadata could not be accessed.")
            print("--Logged parse error. Redownload origin file.")
            log_name = "parse-error"
            log_message = "had an error parsing the yaml and the metadata could not be accessed. Redownload the origin file"
            log_list = None
            log_outcomes(directory, log_name, log_message, log_list)
            parse_error += 1  # variable will increment every loop iteration
            return genre_origin, original_date, release_type

        # check to see if the origin file has the corect metadata
        if "Cover" in data.keys():
            print("--You are using the correct version of gazelle-origin.")
            print("--Origin tags found.")

            # turn the data into variable
            genre_origin = data["Tags"]
            release_type = data["Release type"]
            original_date = data["Original year"]

            if genre_origin != None:
                print(f"--Origin genre tags are -> {genre_origin}")
                # remove spaces in comma delimited string
                genre_origin = genre_origin.replace(" ", "")
                # turn string into list
                genre_origin = genre_origin.split(",")
                return genre_origin, original_date, release_type
            else:
                # log the missing genre tag information in origin file
                print("--There are no genre tags in the origin file.")
                print("--Logged missing genre tag in origin file.")
                log_name = "missing_genre_origin"
                log_message = "genre tag missing in origin file"
                log_list = None
                log_outcomes(directory, log_name, log_message, log_list)
                missing_genre_origin += 1  # variable will increment every loop iteration

                if genre_origin != None:
                    pass
                elif release_type == "Soundtrack":
                    pass
                else:
                    genre_origin = "genre.missing"
                    # Pass the directory to the move_location function so it can be added to the move_list and moved if the move flag is turned on
                    if move_flag == True:
                        move_location(directory)
                    else:
                        pass
                return genre_origin, original_date, release_type
        else:
            print("--You need to update your origin files with more metadata.")
            print("--Switch to the gazelle-origin fork here: https://github.com/spinfast319/gazelle-origin")
            print("--Then run: https://github.com/spinfast319/Update-Gazelle-Origin-Files")
            print("--Then try this script again.")
            print("--Logged out of date origin file.")
            log_name = "out-of-date-origin"
            log_message = "origin file out of date"
            log_list = None
            log_outcomes(directory, log_name, log_message, log_list)
            genre_origin = []
            origin_old += 1  # variable will increment every loop iteration
            return genre_origin, original_date, release_type
    else:
        # log the missing origin file folders that are not likely supposed to be missing
        print("--An origin file is missing from a folder that should have one.")
        print("--Logged missing origin file.")
        log_name = "bad-missing-origin"
        log_message = "origin file is missing from a folder that should have one"
        log_list = None
        log_outcomes(directory, log_name, log_message, log_list)
        bad_missing += 1  # variable will increment every loop iteration
        return genre_origin, original_date, release_type


# A function that adds a genre tag if one is missing and there is an associated style using regular expressions
def map_genre_reg(genre_origin):

    print("--Mapping genre's with regex")
    # A list that holds pairs of genres and their associated regular expression
    reg_map = [
        ("electronic", "house$"),
        ("electronic", "techno$"),
        ("electronic", "trance$"),
        ("house", ".house$"),
        ("techno", ".techno$"),
        ("trance", ".trance$"),
        ("metal", ".metal$"),
        ("rock", ".rock$"),
        ("jazz", ".jazz$"),
        ("country", ".country$"),
        ("classical", ".classical$"),
        ("hip.hop", ".hip.hop$"),
        ("hip.hop", ".rap$"),
        ("punk.ska", ".punk$"),
    ]

    # A list of genres that should be skipped in the regex mapping
    skip_list = [
        "post.rock",
        "future.jazz",
        "acid.jazz",
        "nu.jazz",
        "new.jazz",
        "downtempo.future.jazz",
        "chiptune.jazz",
        "hair.metal",
        "funk.metal",
        "electro.punk",
        "dance.punk",
        "post.punk",
        "contemporary.post.punk",
        "synth.punk",
        "disco.punk",
        "gypsy.punk",
        "indian.classical",
        "cinematic.classical",
    ]

    for j in reg_map:
        if j[0] not in genre_origin:
            for i in genre_origin:
                if i in skip_list:
                    pass
                else:
                    match = re.search(j[1], i)
                    if match:
                        genre_origin.append(j[0])
                        print(f"----Added {j[0]} to genre list because {i} was there.")

    #  turn list into set to get rid of duplicates
    genre_origin = set(genre_origin)
    #  turn set back into list to not break things
    genre_origin = list(genre_origin)

    return genre_origin


# A function that adds a genre tag if one is missing and there is an associated style using a list of paired genre/styles
def map_genre_list(genre_origin):

    # Open CSV of alias mappings, create list of tuples
    with open(os.path.join(__location__, "genre-map.csv"), encoding="utf-8") as f:
        reader = csv.reader(f)
        genre_map = list(tuple(line) for line in reader)

    #  Loop through the list and replace any term with it's proper alias
    print("--Mapping genre's with list")
    for i in genre_map:
        if i[0] in genre_origin:
            # print(f"--{i[0]} already in genre list")
            pass
        else:
            if i[1] in genre_origin:
                genre_origin.append(i[0])
                print(f"----Added {i[0]} to genre list because {i[1]} was there. ")

    return genre_origin


# A function to add soundtrack to list of genres in origin file list
def merge_soundtrack(genre_origin, release_type):

    print(f"--Checking release type.")
    print(f"--This is a {release_type}")

    if release_type == "Soundtrack":
        release_type = "soundtrack"
        if genre_origin == None:
            genre_origin = [release_type]
            print(f"--Adding Soundtrack to the genre tags in origin file")
            genre_origin_string = ", ".join(genre_origin)
            print(f"----Origin genre tags are -> {genre_origin_string}")
        else:
            if release_type in genre_origin:
                pass
                print(f"--Genre soundtrack already in origin")
            else:
                print(f"--Adding soundtrack to the genre tags in origin file")
                genre_origin.append(release_type)
                genre_origin_string = ", ".join(genre_origin)
                print(f"--Origin genre tags are -> {genre_origin_string}")

    return genre_origin


# A function to check to see if a genre decade tag is the same as the decade the original year the album was released and removes it if it is
def clean_years(genre_origin, original_date):

    # A list of dacades to check
    check_list = ["1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]

    print("--Comparing decades to orignal year and removing if matched.")
    for i in genre_origin:
        if i in check_list:
            i_short = i[0:3]
            original_date = str(original_date)
            original_date_short = original_date[0:3]
            if i_short == original_date_short:
                genre_origin.remove(i)
                print(f"----Removed {i} from list of genres due to the album being released in {original_date}.")
            else:
                print(f"----This album has was released in {original_date} but has music from the {i}.")
                pass
        else:
            pass

    return genre_origin


# A function to remove genres that we don't want written to tags
def remove_genre(genre_origin):

    # A list of genres that should be removed
    remove_list = [
        "freely.available",
        "hardcore.to.sort",
        "other",
        "misc",
        "miscellaneous",
        "delete.this.tag",
        "unknown",
        "various.artists",
        "танцевальная.музыка",
        "альтернативная.музыка",
        "злектронная.музыкаа",
        " ",
        "",
        None,
    ]

    print("--Looking for genres to remove.")
    for i in genre_origin:
        for j in remove_list:
            if i == j:
                genre_origin.remove(j)
                print(f"----Removed {j} from list of genres.")
            else:
                pass

    return genre_origin


# A function to remove pop as a genre if it is indie.pop
def strict_pop(genre_origin):

    # A list of types of pop stules that should not have pop as a genre
    remove_list = ["indie.pop", "indie.rock", "indie"]

    print("--Looking for styles of pop that don't fit in the pop genre.")
    for i in genre_origin:
        for j in remove_list:
            if i == j:
                if "pop" in genre_origin:
                    genre_origin.remove("pop")
                    print(f"--Removed pop from list of genres.")
            else:
                pass

    return genre_origin


# A function to add non.music as a genre if it is missing and the correct styles are present
def add_non_music(genre_origin):

    # A list of all the genre tags
    total_genre = [
        "blues",
        "childrens.music",
        "classical",
        "country",
        "electronic",
        "folk",
        "hip.hop",
        "jazz",
        "lounge",
        "metal",
        "noise",
        "non.music",
        "pop",
        "post.rock",
        "punk.ska",
        "rock",
        "rhythm.and.blues",
        "soundtrack",
        "world.music",
    ]

    # A list of genres that can be associated with non.music
    non_music_list = [
        "comedy",
        "spoken.word",
        "stand.up",
        "special.effects",
        "movie.effects",
        "special.effects",
        "foley",
        "poetry",
        "birds",
        "bird.songs",
        "bird.sounds",
        "bird.calls",
        "nature",
        "ocean",
        "waves",
        "rain",
        "thunder",
        "fire",
        "animal.sounds",
        "whale.song",
        "whales",
        "frogs",
        "insects",
        "humour",
    ]

    print("--Looking for albums of non-music and assigning that as the genre.")
    if any(x in genre_origin for x in total_genre):
        pass
    else:
        if any(y in genre_origin for y in non_music_list):
            genre_origin.append("non.music")
            print("----Added non.music to the list of genres.")
        else:
            pass

    return genre_origin


# A function to write the full genre list back to the origin file
def write_origin(all_genres, origin_location):

    # Turn genre list into a string
    genre_string = ", ".join(all_genres)

    # Load custom representer and yaml config
    ruamel.yaml.representer.RoundTripRepresenter.add_representer(type(None), _represent_none)
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.allow_unicode = True
    yaml.encoding = "utf-8"
    yaml.width = 4096

    # Open origin.yaml file
    with open(origin_location, encoding="utf-8") as f:
        data = yaml.load(f)
        print("----Opened yaml")

    # Update origin.yaml key value for tags
    data["Tags"] = genre_string
    print("----Updated yaml")

    # Write new origin.yaml file
    with open(origin_location, "w", encoding="utf-8") as f:
        yaml.dump(data, f)
        print("----Wrote yaml")


# A function to turn a list of genres into a nicely formated string
def convert_string(genre_list, sep_char):

    # Alphabetize list
    genre_list.sort()

    if sep_char == ",":
        genre_string = ", ".join(genre_list)
    if sep_char == ";":
        genre_string = "; ".join(genre_list)

    genre_string = genre_string.replace(".", " ")
    genre_string = string.capwords(genre_string, sep=None)
    capital_styles = [
        ("Idm", "IDM"),
        ("Edm", "EDM"),
        ("Ebm", "EBM"),
        ("Asmr", "ASMR"),
        ("Dj", "DJ"),
        ("DJent", "Djent"),
        ("Uk Garage", "UK Garage"),
        ("Uk Bass", "UK Bass"),
        ("Uk House", "UK House"),
        ("Uk Funky", "UK Funky"),
        ("Hi Nrg", "Hi NRG"),
        ("Mpb", "MPB"),
        ("Nwobhm", "NWOBHM"),
        ("Punk Ska", "Punk/Ska"),
    ]

    # capitalize styles that should be
    for i in capital_styles:
        if i[0] in genre_string:
            genre_string = genre_string.replace(i[0], i[1])

    return genre_string


# A function to break the genres into lists of seperate genres and styles
def seperate_genres(genre_origin, directory):
    global missing_final_genre

    print("--Seperating genres into genres and styles.")
    total_genre = [
        "blues",
        "childrens.music",
        "classical",
        "country",
        "electronic",
        "folk",
        "hip.hop",
        "jazz",
        "lounge",
        "metal",
        "noise",
        "non.music",
        "pop",
        "post.rock",
        "punk.ska",
        "rock",
        "rhythm.and.blues",
        "soundtrack",
        "world.music",
    ]
    final_genre = []
    final_style = []

    for i in genre_origin:
        if i in total_genre:
            final_genre.append(i)
        else:
            final_style.append(i)

    if final_genre != []:

        sep_char = ","
        final_genre_string = convert_string(final_genre, sep_char)
        final_style_string = convert_string(final_style, sep_char)
        print(f"Final Genres-> {final_genre_string}")
        print(f"Final Styles-> {final_style_string}")

        return final_genre, final_style

    else:
        # Pass the directory to the move_location function so it can be added to the move_list and moved if the move flag is turned on
        if move_flag == True:
            print("--No genre could be mapped from the tags so no tags will be written to.")
            log_name = "missing_final_genre"
            log_message = "final genre tag not identified and missing"
            log_list = None
            log_outcomes(directory, log_name, log_message, log_list)
            missing_final_genre += 1  # variable will increment every loop iteration
            move_location(directory)
        else:
            pass

        return final_genre, final_style


# A function to write the vorbis genre and style comments
def write_tags(directory, genre, style, album_name):
    global count
    global track_count

    print("--Retagging files.")

    # Turn the genre and style lists into strings with semi-colons seperating the values and re-format them
    sep_char = ";"
    genre_string = convert_string(genre, sep_char)
    style_string = convert_string(style, sep_char)

    # Clear the list so the log captures just this albums tracks
    retag_list = []

    if genre != None:
        # Loop through the directory and rename flac files
        for fname in os.listdir(directory):
            if fname.lower().endswith(".flac"):
                tag_metadata = mutagen.File(fname)
                print(f"----Track Name: {fname}")
                # log track that was retagged
                retag_list.append(f"--Track Name: {fname}")
                #  retag the metadata
                tag_metadata["GENRE"] = genre_string
                tag_metadata["STYLE"] = style_string
                tag_metadata.save()
                track_count += 1  # variable will increment every loop iteration
        count += 1  # variable will increment every loop iteration
    else:
        print(f"Origin metadata unexpectedly missing.")

    # figure out how many tracks were renamed
    tracks_retagged = len(retag_list)
    if tracks_retagged != 0:
        print(f"--Tracks Retagged: {tracks_retagged}")
    else:
        print(f"--There were no flac in this folder.")
    # log the album the name change
    log_name = "files_retagged"
    log_message = f"had {tracks_retagged} files retagged"
    log_list = retag_list
    log_outcomes(directory, log_name, log_message, log_list)


# A function to build the location the files should be moved to
def move_location(directory):
    global sort_directory
    global move_list
    global album_depth

    print(f"MOVE SOURCE: {directory}")
    # create target path

    # get album name or artist-album name and create target path
    path_parths = directory.split(os.sep)
    if album_depth == 1:
        album_name = path_parths[-1]
        target = os.path.join(sort_directory, album_name)
        print(f"MOVE TARGET: {target}")
    elif album_depth == 2:
        artist_name = path_parths[-2]
        album_name = path_parths[-1]
        target = os.path.join(sort_directory, artist_name, album_name)
        print(f"MOVE TARGET: {target}")

    print("--This should be moved to the Genre Sort folder and has been added to the move list.")
    # make the pair a tupple
    move_pair = (directory, target)
    # adds the tupple to the list
    move_list.append(move_pair)


# A function to move albums to the correct folder
def move_albums(move_list):
    global move_count

    # Loop through the list of albums to move
    for i in move_list:

        # Break each entry into a source and target
        start_path = i[0]
        target = i[1]

        # Move them to the folders they belong in
        print("")
        print("Moving.")
        print(f"--Source: {start_path}")
        print(f"--Destination: {target}")
        shutil.move(start_path, target)
        print("Move completed.")
        move_count += 1  # variable will increment every loop iteration
        

# The main function that controls the flow of the script
def main():
    global move_flag
    global move_list

    try:
        # intro text
        print("")
        print("Join me, and together...")
        print("")

        # Get all the subdirectories of album_directory recursively and store them in a list
        directories = osl.set_directory(album_directory)

        #  Run a loop that goes into each directory identified in the list and runs the genre and style writing process
        for i in directories:
            os.chdir(i)  # Change working Directory
            print("")
            print("Writing genres and styles starting.")
            # establish directory level
            origin_location, album_name = level_check(i)
            # check for flac
            is_flac = flac_check(i)
            if is_flac == True:
                # Load orgin genre
                # open orgin file
                genre_origin, original_date, release_type = get_genre_origin(i, origin_location, album_name)

                # Skip if origin file is missing
                if genre_origin == []:
                    print("There was a missing or malformed origin file, check your logs, fix it and rerun.")
                    pass
                # Skip if there are no tags in the origin file
                elif genre_origin == "genre.missing":
                    print("There was no genre in the origin file.")
                    pass
                else:
                    # create a hash of the genre_origine list so we can track it and see if it changes and write changes back to the file at the end
                    print("--Creating a hash of the starting origin genre list.")
                    # alphabetize list
                    if genre_origin != None:
                        genre_origin.sort()
                    genre_hash_start = hashlib.md5(pickle.dumps(genre_origin))

                    # add soundtrack to list of genres in origin file list
                    genre_origin = merge_soundtrack(genre_origin, release_type)
                    # Map tags and assign missing ones using regular expressions
                    genre_origin = map_genre_reg(genre_origin)
                    # Map tags and assign missing ones using a list
                    genre_origin = map_genre_list(genre_origin)
                    # Remove decade tags where the original album release date is in the decade
                    genre_origin = clean_years(genre_origin, original_date)
                    # Remove tags that should not be there
                    genre_origin = remove_genre(genre_origin)
                    # Remove pop as a genre if indie.pop
                    genre_origin = strict_pop(genre_origin)
                    # Add non.music as a genre if no other genre is present and the right other tags are there
                    genre_origin = add_non_music(genre_origin)

                    # check if the orgin tag has been updated and write updated tags to the origin file if it has
                    # create a hash of the genre_origin list so we can track it and see if it changes and write changes back to the file at the end
                    # alphabetize list
                    if genre_origin != None:
                        genre_origin.sort()
                    genre_hash_end = hashlib.md5(pickle.dumps(genre_origin))
                    print("--Comparing original origin genre list to final genre list.")
                    print(f"----Genre Hash Start: {genre_hash_start.hexdigest()}")
                    print(f"----Genre Hash End  : {genre_hash_end.hexdigest()}")

                    # Write tags to origin file if any are added
                    if genre_hash_start.hexdigest() != genre_hash_end.hexdigest():
                        print("--Genre list has been updated.")
                        print("--Writing genre to origin file.")
                        write_origin(genre_origin, origin_location)
                        written_genre_string = ", ".join(genre_origin)
                        print(f"--Final genres writen to origin file -> {written_genre_string}")
                    else:
                        print("--Genre list has note been updated.")
                        print("--No new genre tags to add to origin genre.")

                    # Make one list of genres and one of styles
                    genre, style = seperate_genres(genre_origin, i)
                    if genre != []:
                        # Write genre and style to vorbis
                        write_tags(i, genre, style, album_name)
                        print("Genre and style tags written to album.")
                    else:
                        # Log missing genres
                        print("This album did not have a genre that mapped to anything. Please check the log and manually fix it.")
            else:
                print("No flac files.")

        # Move the albums to the folders the need to be sorted into
        if move_flag == True:

            # Change directory so the album directory can be moved and move them
            os.chdir(log_directory)

            print("")
            print("Part 2: Moving")

            # Move the albums
            if move_list == []:
                print("--No albums needed moving.")
            else:
                move_albums(move_list)

    finally:
        # Summary text
        print("")
        print("...we can rule the galaxy as father and son.")
        # run summary text function to provide error messages
        summary_text()
        print("")


if __name__ == "__main__":
    main()
