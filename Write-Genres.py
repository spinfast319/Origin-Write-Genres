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


#  Set your directories here
album_directory = "M:\Python Test Environment\Albums"  # Which directory do you want to start with?
log_directory = "M:\Python Test Environment\Logs"  # Which directory do you want the log in?
genre_map_list = "M:\music-util\origin-scripts\Combine-Genres\genre-map.csv"  # Set the location of the genre-map.csv file.

# Set whether you are using nested folders or have all albums in one directory here
# If you have all your ablums in one music directory Music/Album_name then set this value to 1
# If you have all your albums nest in a Music/Artist/Album style of pattern set this value to 2
# The default is 1
album_depth = 1

# Establishes the counters for completed albums and missing origin files
count = 0
total_count = 0
error_message = 0
good_missing = 0
bad_missing = 0
parse_error = 0
origin_old = 0
missing_origin_genre = 0
missing_genre = 0
missing_tags = 0

# identifies album directory level
path_segments = album_directory.split(os.sep)
segments = len(path_segments)
album_location_check = segments + album_depth


# A function to log events
def log_outcomes(directory, log_name, message, log_list):
    global log_directory

    script_name = "Origin Write Tags Script"
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
    global missing_origin_genre

    print("")
    print(f"This script wrate tags for {count} albums out of {total_count} albums.")
    print("This script looks for potential missing files or errors. The following messages outline whether any were found.")

    error_status = error_exists(parse_error)
    print(f"--{error_status}: There were {parse_error} albums skipped due to not being able to open the yaml. Redownload the yaml file.")
    error_status = error_exists(origin_old)
    print(f"--{error_status}: There were {origin_old} origin files that do not have the needed metadata and need to be updated.")
    error_status = error_exists(bad_missing)
    print(f"--{error_status}: There were {bad_missing} folders missing an origin files that should have had them.")
    error_status = error_exists(missing_origin_genre)
    print(f"--{error_status}: There were {missing_origin_genre} folders missing genre tags in their origin files.")
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

    # Loop through the directory and see if any file is a flac
    for fname in os.listdir(directory):
        if fname.endswith(".flac"):
            print("--There are flac in this directory.")
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
def get_origin_genre(directory, origin_location, album_name):
    global parse_error
    global origin_old
    global bad_missing
    global missing_origin_genre

    print(f"--Getting metadata for {album_name}")
    print(f"--From: {origin_location}")

    # check to see if there is an origin file is supposed to be in this specific directory
    file_exists = check_file(directory)
    # check to see the origin file location variable exists
    location_exists = os.path.exists(origin_location)

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
            return
        # check to see if the origin file has the corect metadata
        if "Cover" in data.keys():
            print("--You are using the correct version of gazelle-origin.")

            # turn the data into variable
            origin_genre = data["Tags"]
            release_type = data["Release type"]
            if origin_genre != None:
                # remove spaces in comma delimited string
                origin_genre = origin_genre.replace(" ", "")
                # turn string into list
                origin_genre = origin_genre.split(",")
                return origin_genre, release_type
            else:
                # log the missing genre tag information in origin file
                print("--There are no genre tags in the origin file.")
                print("--Logged missing genre tag in origin file.")
                log_name = "missing_origin_genre"
                log_message = "genre tag missing in origin file"
                log_list = None
                log_outcomes(directory, log_name, log_message, log_list)
                missing_origin_genre += 1  # variable will increment every loop iteration
                origin_genre = "genre.missing"
                return origin_genre, release_type
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
            origin_old += 1  # variable will increment every loop iteration


# Change this to write
# A function to get the vorbis genre, style and mood tags
def get_vorbis_genre(directory, album_name):

    print("--Checking for genre, style and mood tags.")

    # Open track in directory and see if genre tag is populated
    for fname in os.listdir(directory):
        if fname.endswith(".flac"):
            missing_count = 0
            genre = []
            tag_metadata = mutagen.File(fname)
            if "GENRE" in tag_metadata:
                print("--Genre tag found.")
                genre.extend(tag_metadata["GENRE"])
                print(genre)
            else:
                print("--No genre tag.")
                missing_count += 1
            if "STYLE" in tag_metadata:
                print("--Style tag found.")
                genre.extend(tag_metadata["STYLE"])
                print(tag_metadata["STYLE"])
            else:
                print("--No style tag.")
                missing_count += 1
            if "MOOD" in tag_metadata:
                print("--Mood tag found.")
                genre.extend(tag_metadata["MOOD"])
                print(tag_metadata["MOOD"])
            else:
                print("--No mood tag.")
                missing_count += 1

            if missing_count == 3:
                print("No vorbis tags found.")
                break
            else:
                print("--Combined genre, style and mood tags.")
                print(genre)
                # Clean and standardize the genre
                cleaned_genre = clean_genre(genre)
                # this is for the output and nothing else.
                print("--Cleaned tags.")
                print(cleaned_genre)
                genre_list = ", ".join(cleaned_genre)
                # print (f" The genre tag is {genre_list}.")
                return cleaned_genre


# A function to remove any null values from strings
def clean_string_null(string_to_clean):
    each_char = list(string_to_clean)
    clean_track = []
    for i in each_char:
        if i == "\x00":
            print("--Bad character removed")
        else:
            clean_track.append(i)
    clean_string = "".join(clean_track)
    return clean_string


# probably delete this
# A function to clean up and standardize the vorbis tags
def clean_genre(genre):
    # this first part standardizes the seperating characters around commas
    # make genre lowercase
    genre_lower = [tag.lower() for tag in genre]
    # replace //// with ,
    genre_noslash = [tag.replace("////", ",") for tag in genre_lower]
    # replace /// with ,
    genre_noslash = [tag.replace("///", ",") for tag in genre_noslash]
    # replace // with ,
    genre_noslash = [tag.replace("//", ",") for tag in genre_noslash]
    # replace / with ,
    genre_noslash = [tag.replace("/", ",") for tag in genre_noslash]
    # replace \\\\ with ,
    genre_noslash = [tag.replace("\\\\", ",") for tag in genre_noslash]
    # replace \\ with ,
    genre_noslash = [tag.replace("\\", ",") for tag in genre_noslash]
    # replace | with ,
    genre_nopipe = [tag.replace("|", ",") for tag in genre_noslash]
    # replace ｜ with ,
    genre_nopipe = [tag.replace("｜", ",") for tag in genre_nopipe]
    # replace ; with ,
    genre_nosemi = [tag.replace(";", ",") for tag in genre_nopipe]

    # this second part uses the standardized seperators to make a new list with each item independent
    # turn list into string
    genre_string = ", ".join(genre_nosemi)
    # turn string into list seperating tags by comma
    genre_list = genre_string.split(",")

    # this third part cleans or standardizes each genre tag
    # strip tags
    genre_strip = [tag.strip() for tag in genre_list]
    # remove null characters
    gernre_nonull = [clean_string_null(tag) for tag in genre_strip]
    # replace - with .
    genre_nodash = [tag.replace("-", ".") for tag in gernre_nonull]
    # replace _ with .
    genre_nounder = [tag.replace("_", ".") for tag in genre_nodash]
    # replace & with and
    genre_noamp = [tag.replace("&", "and") for tag in genre_nounder]
    # replace dnb with drum.and.bass
    genre_clean = [tag.replace("dnb", "drum.and.bass") for tag in genre_noamp]
    # replace d n b with drum.and.bass
    genre_clean = [tag.replace("d n b", "drum.and.bass") for tag in genre_clean]
    # replace drum n bass with drum.and.bass
    genre_clean = [tag.replace("drum n bass", "drum.and.bass") for tag in genre_clean]
    # replace dandb with drum.and.bass
    genre_clean = [tag.replace("dandb", "drum.and.bass") for tag in genre_clean]
    # replace d and b with drum.and.bass
    genre_clean = [tag.replace("d and b", "drum.and.bass") for tag in genre_clean]
    # replace drumnbass with drum.and.bass
    genre_clean = [tag.replace("rhythmnblues", "drum.and.bass") for tag in genre_clean]
    # replace drumandbass with drum.and.bass
    genre_clean = [tag.replace("rhythmandblues", "drum.and.bass") for tag in genre_clean]
    # replace jungle with drum.and.bass
    genre_clean = [tag.replace("jungle", "drum.and.bass") for tag in genre_clean]
    # replace rnb with rhythm.and.blues
    genre_clean = [tag.replace("rnb", "rhythm.and.blues") for tag in genre_clean]
    # replace r n b with rhythm.and.blues
    genre_clean = [tag.replace("r n b", "rhythm.and.blues") for tag in genre_clean]
    # replace rythym n blues with rhythm.and.blues
    genre_clean = [tag.replace("rythym n blues", "rhythm.and.blues") for tag in genre_clean]
    # replace randb with rhythm.and.blues
    genre_clean = [tag.replace("randb", "rhythm.and.blues") for tag in genre_clean]
    # replace r and b with rhythm.and.blues
    genre_clean = [tag.replace("r and b", "rhythm.and.blues") for tag in genre_clean]
    # replace rhythmnblues with rhythm.and.blues
    genre_clean = [tag.replace("rhythmnblues", "rhythm.and.blues") for tag in genre_clean]
    # replace rhythmandblues with rhythm.and.blues
    genre_clean = [tag.replace("rhythmandblues", "rhythm.and.blues") for tag in genre_clean]
    # replace world with world.music
    genre_clean = [tag.replace("world", "world.music") for tag in genre_clean]
    # replace worldmusic with world.music
    genre_clean = [tag.replace("worldmusic", "world.music") for tag in genre_clean]
    # replace down tempo with downtempo
    genre_clean = [tag.replace("down tempo", "downtempo") for tag in genre_clean]
    # replace avantgarde with avant.garde
    genre_clean = [tag.replace("avantgarde", "avant.garde") for tag in genre_clean]
    # replace triphop with trip.hop
    genre_clean = [tag.replace("triphop", "trip.hop") for tag in genre_clean]
    # replace electronica with electronic
    genre_clean = [tag.replace("electronica", "electronic") for tag in genre_clean]
    # replace house deep with deep.house
    genre_clean = [tag.replace("house deep", "deep.house") for tag in genre_clean]
    # replace ambiant with ambient
    genre_clean = [tag.replace("ambiant", "ambient") for tag in genre_clean]
    # replace space with .
    genre_nospace = [tag.replace(" ", ".") for tag in genre_clean]
    # standardize tag spelling against RED alias mapping
    cleaned_genre = [RED_alias(tag) for tag in genre_nospace]
    return cleaned_genre


# change this to genre_map
# A function to use RED alias tags to have consistency in genres
def RED_alias(genre):
    global genre_map_list

    # Open CSV of alias mappings, create list of tuples
    with open(RED_alias_list, encoding="utf-8") as f:
        reader = csv.reader(f)
        RED_list = list(tuple(line) for line in reader)

    #  Loop through the list and replace any term with it's proper alias
    for i in RED_list:
        if genre == i[0]:
            genre = i[1]
            print("--Standardized with RED alias")

    return genre


# probably delete this
# A function to compare and merge the vorbis and origin genre tags
def merge_genres(genre_vorbis, genre_origin, album_name):

    print("--Origin tags found.")
    print(genre_vorbis)
    print(genre_origin)

    # Set a flag to check whether the origin genre is updated
    diff_flag = False

    for i in genre_vorbis:
        if i in genre_origin:
            pass
            # print(f"--Genre {i} already in origin")
        else:
            # print(f"--Adding {i} to the genre tags in origin file")
            genre_origin.append(i)
            diff_flag = True

    # print("--The vorbis and origin tags have been cleaned and combined.")
    print(genre_origin)
    return genre_origin, diff_flag


# write the full genre list back to the origin file
def write_origin(all_genres, origin_location):
    global count

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
        print("--Opened yaml")

    # Update origin.yaml key value for tags
    data["Tags"] = genre_string
    print("--Updated yaml")

    # Write new origin.yaml file
    with open(origin_location, "w", encoding="utf-8") as f:
        yaml.dump(data, f)
        print("--Wrote yaml")
        print("Genre tags have been merged successfully.")
        count += 1  # variable will increment every loop iteration


# The main function that controls the flow of the script
def main():

    try:
        # intro text
        print("")
        print("Join me, and together...")
        print("")

        # Get all the subdirectories of album_directory recursively and store them in a list:
        directories = [os.path.abspath(x[0]) for x in os.walk(album_directory)]
        directories.remove(os.path.abspath(album_directory))  # If you don't want your main directory included

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
                origin_exists = check_file(i)  # Determine if folder should have origin file and if it does
                if origin_exists == True:
                    genre_origin, release_type = get_origin_genre(i, origin_location, album_name)
                    print(genre_origin)
                    print(release_type)
                # Merge in soundtrack
                # Map tags and assign missing ones
                # Write tags to origin file if any are added
                # Make a list of genres
                # Make a list of styles
                # Write genre and style to vorbis
                """
                # check if vorbis tag for genre is populated
                genre_vorbis = get_vorbis_genre(i, album_name)
                if genre_vorbis != None:
                    # open orgin file
                    genre_origin, release_type = get_origin_genre(i, origin_location, album_name)
                    if genre_origin == None:
                        pass
                    elif genre_origin == "genre.missing":
                        # if the origin file does not have a genre and the vorbis exists then write vorbis tag to origin
                        write_origin(genre_vorbis, origin_location)
                    else:     
                        # merge the genre tags
                        all_genres, diff_flag = merge_genres(genre_vorbis, genre_origin, album_name)
                        # if there is an update write genre to tag key value pair
                        if diff_flag == True:
                            write_origin(all_genres, origin_location)
                        else:
                            print("No new genre tags to add to origin genre")
                else:
                    print("No genre tag.")
                """
            else:
                print("No flac files.")

    finally:
        # Summary text
        print("")
        print("...we can rule the galaxy as father and son.")
        # run summary text function to provide error messages
        summary_text()
        print("")


if __name__ == "__main__":
    main()
