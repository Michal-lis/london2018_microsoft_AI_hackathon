#   __  __       _       _        ____
#  |  \/  | __ _| |_ ___| |__    / ___| __ _ _ __ ___   ___
#  | |\/| |/ _` | __/ __| '_ \  | |  _ / _` | '_ ` _ \ / _ \
#  | |  | | (_| | || (__| | | | | |_| | (_| | | | | | |  __/
#  |_|  |_|\__,_|\__\___|_| |_|  \____|\__,_|_| |_| |_|\___|
#
botName = 'michallis9-defbot'
import requests
import json
from random import sample, choice
from time import sleep

headers_vision = {'Ocp-Apim-Subscription-Key': '8dd544795f6247a68d9acfd698417043'}
vision_base_url = "https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/anlayse"


# =============================================================================
# calculate_move() overview
#  1. Analyse the upturned tiles and remember them
#  2. Determine if you have any matching tiles
#  3. If we have matching tiles:
#        use them as a move
#  4. If no matching tiles:
#        Guess two tiles for this move
#  Get more help at http://help.aigaming.com/match-game
#
def calculate_move(gamestate):
    # Record the number of tiles in the game
    # so we know how many tiles we need to loop through
    num_tiles = len(gamestate["Board"])
    if "Failed moves" not in persistent_data.keys():
        persistent_data["Failed moves"] = []
    # Set up persistent data variables to remember information
    # between calls to calculate_move.
    # (Click the book icon on the right to get more information
    # on persistent data) ----------------->
    # If we have not yet added "AnalysedTiles" to persistent_data
    # (i.e. It is the first turn)
    if "AnalysedTiles" not in persistent_data:
        # Create a list of tile information
        persistent_data["AnalysedTiles"] = []
        for index in range(num_tiles):
            # Mark tile as not analysed
            persistent_data["AnalysedTiles"].append({})
            persistent_data["AnalysedTiles"][index]["State"] = "UNANALYSED"
            persistent_data["AnalysedTiles"][index]["Subject"] = None

    # If there are upturned tiles from our last turn.
    # The very first move you make does not have any upturned tiles, and
    # if your last move matched tiles, you will not have any upturned tiles
    if gamestate["UpturnedTiles"] != []:
        if "PreviousMove" in persistent_data:
            persistent_data["Failed moves"].append(persistent_data["AnalysedTiles"][persistent_data["PreviousMove"])
            # Analyse the tiles images using the Microsoft API and
            # store results in persistent_data
            analyse_tiles(gamestate["UpturnedTiles"], gamestate)

            # If it is our first turn, or our previous move was a match
            else:
            # If it is not our first move of the game
            # Then our previous move successfully matched two tiles
            if "PreviousMove" in persistent_data:
                persistent_data["AnalysedTiles"][persistent_data["PreviousMove"][0]]["State"] = "MATCHED"
            persistent_data["AnalysedTiles"][persistent_data["PreviousMove"][1]]["State"] = "MATCHED"
            print("Persistent Data: {}".format(persistent_data))

            # Check the stored tile information in persistent_data
            # to see if there are any matching tiles
            match = search_for_matching_tiles()
            # If we have found a matching pair
            if match is not None:
            # Print out the move for debugging ----------------->
                print("Matching Move: {}".format(match))
            # Set our move to be these matching tiles
            move = match
            # If we don't have any matching tiles
            else:
            # Create a list of all the unanalysed tiles
            unanalysed_tiles = get_unanalysed_tiles()
            # If there are tiles we haven't analysed yet
            if unanalysed_tiles != []:
            # Choose the unanalysed tiles that you want to turn over
            # in your next move. We turn over a random pair of
            # unanalysed tiles, but, could you make a more intelligent
            # choice?

                move = sample(unanalysed_tiles, 2)

            # Print out the move here ----------------->
            print("New Tiles Move: {}".format(move))
            # If the unanalysed_tiles list is empty (all tiles have been analysed)
            else:
            print("ALL TILES ANALYSED!\n\n\n")
            # If all else fails, we will need to manually match each tile

            # Create a list of all the unmatched tiles
            unmatched_tiles = get_unmatched_tiles()
            move = sample(unmatched_tiles, 2)
            if move in persistent_data["Failed moves"]:
                pass

            # Print the move out here ----------------->
            print("Random Combination Move: {}".format(move))

            # Store our move in persistent_data to look back at next turn
            persistent_data["PreviousMove"] = move
            # Print out the current gamestate here ----------------->
            print("Gamestate: {}".format(json.dumps(gamestate)))
            # Return the move we wish to make
    return {"Tiles": move}


def get_unmatched_tiles():
    # Create a list of all the unmatched tiles
    unmatched_tiles = []
    # For every tile in the game
    for index, tile in enumerate(persistent_data["AnalysedTiles"]):
        # If that tile hasn't been matched yet
        if tile["State"] != "MATCHED":
            # Add that tile to the list of unmatched tiles
            unmatched_tiles.append(index)
    # Return the list
    return unmatched_tiles


def get_unanalysed_tiles():
    # Filter out analysed tiles
    unanalysed_tiles = []
    # For every tile that hasn't been matched
    for index, tile in enumerate(persistent_data["AnalysedTiles"]):
        # If the tile hasn't been analysed
        if tile["State"] == "UNANALYSED":
            # Add that tile to the list of unanalysed tiles
            unanalysed_tiles.append(index)
    # Return the list
    return unanalysed_tiles


def analyse_tiles(tiles, gamestate):
    # For every tile in the list 'tiles'
    for tile in tiles:
        # Call the analyse_tile function with that tile, along with the gamestate
        analyse_tile(tile, gamestate)


def analyse_tile(tile, gamestate):
    # If we have already analysed the tile
    if persistent_data["AnalysedTiles"][tile["Index"]]["State"] != "UNANALYSED":
        # We don't need to analyse the tile again, so stop
        return

    # Call analysis
    analyse_url = vision_base_url + "analyze"
    params_analyse = {'visualFeatures': 'categories,tags,description,faces,imageType,color,adult',
                      'details': 'celebrities,landmarks'}
    data = {"url": tile["Tile"]}
    msapi_response = microsoft_api_call(analyse_url, params_analyse, headers_vision, data)
    print(msapi_response)

    # Call ocr
    ocr_url = vision_base_url + "ocr"
    params_ocr = {'language': 'unk', 'detectOrientation ': 'true'}
    data = {"url": tile["Tile"]}
    msapi_response = microsoft_api_call(ocr_url, params_ocr, headers_vision, data)

    # Check if the subject of the tile is an animal
    subject = check_for_animal(msapi_response, gamestate["AnimalList"])
    # If we haven't determined the subject of the image yet
    if subject is None:
        # Check if the subject of the tile is a landmark
        subject = check_for_landmark(msapi_response)
    # If we still haven't determined the subject of the image yet
    if subject is None:
        subject = check_for_ocr(msapi_response)
        pass
    # Remember this tile by adding it to our list of known tiles
    # Mark that the tile has now been analysed
    persistent_data["AnalysedTiles"][tile["Index"]]["State"] = "ANALYSED"
    persistent_data["AnalysedTiles"][tile["Index"]]["Subject"] = subject


def check_for_ocr(msapi_response):
    subject = None
    if 'language' in msapi_response.keys():
        subject = msapi_response['regions'][0]['lines'][0]['words'][0]['text']
    print("Word: {}".format(subject))
    return subject


def check_for_animal(msapi_response, animal_list):
    # Initialise our subject to None
    subject = None
    # For every tag in the returned tags, in descending confidence order
    for tag in sorted(msapi_response["tags"], key=lambda x: x['confidence'], reverse=True):
        # If the tag has a name and that name is one of the animals in our list
        if "name" in tag and tag["name"] in animal_list:
            # Record the name of the animal that is the subject of the tile
            # (We store the subject in lowercase to make comparisons easier)
            subject = tag["name"].lower()
            # Print out the animal we have found here ----------------->
            print("Animal: {}".format(subject))
            # Exit the for loop
            break
    # Return the subject
    return subject


def check_for_landmark(msapi_response):
    # Initialise our subject to None
    subject = None
    # For every category in the returned categories
    if len(msapi_response["categories"]) != 0:
        subject = msapi_response["categories"][0]["detail"]["landmarks"][0]["name"].lower()
    print("Landmark: {}".format(subject))
    return subject


def search_for_matching_tiles():
    # For every tile subject and its index
    for index_1, tile_1 in enumerate(persistent_data["AnalysedTiles"]):
        # Loop through every tile subject and index
        for index_2, tile_2 in enumerate(persistent_data["AnalysedTiles"]):
            # If the two tile's subject is the same and isn't None and the tile
            # hasn't been matched before, and the tiles aren't the same tile
            if tile_1["State"] == tile_2["State"] == "ANALYSED" and tile_1["Subject"] == tile_2["Subject"] and tile_1[
                "Subject"] is not None and index_1 != index_2:
                # Choose these two tiles
                # Return the two chosen tiles as a list
                return [index_1, index_2]
    # If we have not matched any tiles, return no matched tiles
    return None


def microsoft_api_call(url, params, headers, data):
    # Make API request
    response = requests.post(url, params=params, headers=headers, json=data)
    # Convert result to JSON
    res = response.json()
    # While we have exceeded our request volume quota
    while "statusCode" in res and res["statusCode"] == 429:
        # Wait for 1 second
        sleep(1)
        # Print that we are retrying the API call here ----------------->
        print("Retrying")
        # Make API request
        response = requests.post(url, params=params, headers=headers, json=data)
        # Convert result to JSON
        res = response.json()
    # Print the result of the API call here ----------------->
    print(res)
    # Return JSON result of API request
    return res
