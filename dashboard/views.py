from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from .utils import *
from .database.ID_VAL_PAIRS import PLAYERS
from .database.DB import DB

import time


def index(request):
    return render(request, 'dashboard/index.html')


def compare(request, table_opt=None):
    player_1_name = request.GET.get('player_1')
    player_2_name = request.GET.get('player_2')
    table_opt = request.GET.get('table_opt')
    try:
        last_few_seasons = int(request.GET.get('last_few_seasons'))
    except:
        last_few_seasons = None
    
    # if no player provided
    if player_1_name == None or player_2_name == None:
        return render(request, 'dashboard/compare.html')
    
    # get the player id
    for player in PLAYERS:
        if player[1] == player_1_name:
            player_1_id = player[0]
        if player[1] == player_2_name:
            player_2_id = player[0]
    
    # initialize list to store vizzes
    std_stats_vizzes = []
    shooting_vizzes = []
    passing_vizzes = []
    def_acts_vizzes = []
    
    # scrap players data
    # print("Scraping 1st player...")
    player_1_soup = scrap_player(player_1_id, player_1_name)
    # print("1st player scraped      ")
    # delay for 4 seconds before the next scrap to prevent excessive request in a short period of time and getting blocked
    # source: https://www.sports-reference.com/bot-traffic.html
    # for sec in range(0, 4):
    #     if (10-sec) == 1:
    #         print(f"Delay remaining: {4-sec} second  ", end='\r')  
    #     else:  
    #         print(f"Delay remaining: {4-sec} seconds ", end='\r')
    #     time.sleep(1)
    # print("Scraping 2nd player...        ")
    player_2_soup = scrap_player(player_2_id, player_2_name)
    # print("2nd player scraped      ")
    
    # get specified tables
    if table_opt == "standard_stats":
        player_1_table = clean_standard_stats_table(get_player_table(player_1_soup))
        player_2_table = clean_standard_stats_table(get_player_table(player_2_soup))
        
        # struct a set
        player_A_set = (player_1_name, player_1_table)
        player_B_set = (player_2_name, player_2_table)
        
        # plot vizzes
        std_choices = ["Minutes Played", "Starts", "Matches Played", "90s", "Starts Stack"]
        expected_choices = ["xG", "npxG", "xA", "npxG+xA"]
        for choice in std_choices:
            viz = compare_standard_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            std_stats_vizzes.append(viz)
        for choice in expected_choices:
            viz = compare_standard_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            std_stats_vizzes.append(viz)
        
    elif table_opt == "shooting_stats":
        player_1_table = clean_shooting_stats_table(get_player_table(player_1_soup, table_category="all_stats_shooting"))
        player_2_table = clean_shooting_stats_table(get_player_table(player_2_soup, table_category="all_stats_shooting"))
    
        # struct a set
        player_A_set = (player_1_name, player_1_table)
        player_B_set = (player_2_name, player_2_table)
        
        # plot vizzes
        sht_choices = ["Goals", "Shoot", "SoT", "SoT%", "Sh/90", "SoT/90", "G/Sh", "G/SoT", "Dist", "Goals Stack"]
        expected_choices = ["xG", "npxG", "npxG/Sh", "G-xG", "np:G-xG"]
        for choice in sht_choices:
            viz = compare_shooting_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            shooting_vizzes.append(viz)
        for choice in expected_choices:
            viz = compare_shooting_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            shooting_vizzes.append(viz)
            
    elif table_opt == "passing_stats":
        player_1_table = clean_passing_stats_table(get_player_table(player_1_soup, table_category="all_stats_passing"))
        player_2_table = clean_passing_stats_table(get_player_table(player_2_soup, table_category="all_stats_passing"))
        
        # struct a set
        player_A_set = (player_1_name, player_1_table)
        player_B_set = (player_2_name, player_2_table)
        
        # plot vizzes
        total_choices = ["Total - Passes Completed", "Total - Passes Attempted", "Total - Pass Completion %", "Total - Total Passes Distance", "Total - Progessive Passes Distance", "Total Passes Stack"]
        short_choices = ["Short - Passes Completed", "Short - Passes Attempted", "Short - Pass Completion %"]
        medium_choices = ["Medium - Passes Completed", "Medium - Passes Attempted", "Medium - Pass Completion %"]
        long_choices = ["Long - Passes Completed", "Long - Passes Attempted", "Long - Pass Completion %"]
        other_choices = ["Assists", "xA", "A-xA", "Key Passes", "Final Third Passes", "Passes into Penalty Area", "Crosses into Penalty Area", "Progressive Passes"]
        for choice in total_choices:
            viz = compare_passing_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            passing_vizzes.append(viz)
        for choice in short_choices:
            viz = compare_passing_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            passing_vizzes.append(viz)
        for choice in medium_choices:
            viz = compare_passing_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            passing_vizzes.append(viz)
        for choice in long_choices:
            viz = compare_passing_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            passing_vizzes.append(viz)
        for choice in other_choices:
            viz = compare_passing_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            passing_vizzes.append(viz)
    
    elif table_opt == "defensive_actions_stats":
        player_1_table = clean_def_acts_stats_table(get_player_table(player_1_soup, table_category="all_stats_defense"))
        player_2_table = clean_def_acts_stats_table(get_player_table(player_2_soup, table_category="all_stats_defense"))
        
        # struct a set
        player_A_set = (player_1_name, player_1_table)
        player_B_set = (player_2_name, player_2_table)
        
        # plot vizzes
        tackles_choices = ["Tackles - Tackles", "Tackles - Tackles Won", "Tackles - Def 3rd", "Tackles - Mid 3rd", "Tackles - Att 3rd", "Tackles Area Stack"]
        vs_dribbles_choices = ["Vs Dribbles - Dribblers Tackled", "Vs Dribbles - Tackle Attempt Against Dribblers", "Vs Dribbles - Tackles Against Dribblers %", "Vs Dribbles - Dribbled Past", "Tackle Attempts Against Dribblers Stack"]
        pressures_choices = ["Pressures - Press Attempts", "Pressures - Press Successes", "Pressures - Press Success %", "Pressures Stack", "Pressures - Press in Def 3rd", "Pressures - Press in Mid 3rd", "Pressures - Press in Att 3rd", "Pressures Area Stack"]
        blocks_choices = ["Blocks - Blocks Made", "Blocks - Shots Blocked", "Blocks - Shots on Target Blocked", "Blocks - Passes Blocked"]
        other_choices = ["Interceptions", "Tackles + Interceptions", "Clearences", "Errors Leading to Opponent's Shots"]
        for choice in tackles_choices:
            viz = compare_def_acts_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            def_acts_vizzes.append(viz)
        for choice in vs_dribbles_choices:
            viz = compare_def_acts_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            def_acts_vizzes.append(viz)
        for choice in pressures_choices:
            viz = compare_def_acts_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            def_acts_vizzes.append(viz)
        for choice in blocks_choices:
            viz = compare_def_acts_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            def_acts_vizzes.append(viz)
        for choice in other_choices:
            viz = compare_def_acts_stats_players(player_A_set, player_B_set, comparison=choice, last_few_seasons=last_few_seasons)
            def_acts_vizzes.append(viz)
    
    elif table_opt == None:
        # plot all categories of data
        player_1_std_table = clean_standard_stats_table(get_player_table(player_1_soup))
        player_2_std_table = clean_standard_stats_table(get_player_table(player_2_soup))
        player_1_shooting_table = clean_shooting_stats_table(get_player_table(player_1_soup, table_category="all_stats_shooting"))
        player_2_shooting_table = clean_shooting_stats_table(get_player_table(player_2_soup, table_category="all_stats_shooting"))
        player_1_passing_table = clean_passing_stats_table(get_player_table(player_1_soup, table_category="all_stats_passing"))
        player_2_passing_table = clean_passing_stats_table(get_player_table(player_2_soup, table_category="all_stats_passing"))
        player_1_def_acts_table = clean_def_acts_stats_table(get_player_table(player_1_soup, table_category="all_stats_defense"))
        player_2_def_acts_table = clean_def_acts_stats_table(get_player_table(player_2_soup, table_category="all_stats_defense"))
        
        # struct a set
        player_A_std_set = (player_1_name, player_1_std_table)
        player_B_std_set = (player_2_name, player_2_std_table)
        player_A_shooting_set = (player_1_name, player_1_shooting_table)
        player_B_shooting_set = (player_2_name, player_2_shooting_table)
        player_A_passing_set = (player_1_name, player_1_passing_table)
        player_B_passing_set = (player_2_name, player_2_passing_table)
        player_A_def_acts_set = (player_1_name, player_1_def_acts_table)
        player_B_def_acts_set = (player_2_name, player_2_def_acts_table)
        
        # plot std vizzes
        std_choices = ["Minutes Played", "Starts", "Matches Played", "90s", "Starts Stack"]
        expected_choices = ["xG", "npxG", "xA", "npxG+xA"]
        for choice in std_choices:
            viz = compare_standard_stats_players(player_A_std_set, player_B_std_set, comparison=choice, last_few_seasons=last_few_seasons)
            std_stats_vizzes.append(viz)
        for choice in expected_choices:
            viz = compare_standard_stats_players(player_A_std_set, player_B_std_set, comparison=choice, last_few_seasons=last_few_seasons)
            std_stats_vizzes.append(viz)
        
        # plot shooting vizzes
        sht_choices = ["Goals", "Shoot", "SoT", "SoT%", "Sh/90", "SoT/90", "G/Sh", "G/SoT", "Dist", "Goals Stack"]
        expected_choices = ["xG", "npxG", "npxG/Sh", "G-xG", "np:G-xG"]
        for choice in sht_choices:
            viz = compare_shooting_stats_players(player_A_shooting_set, player_B_shooting_set, comparison=choice, last_few_seasons=last_few_seasons)
            shooting_vizzes.append(viz)
        for choice in expected_choices:
            viz = compare_shooting_stats_players(player_A_shooting_set, player_B_shooting_set, comparison=choice, last_few_seasons=last_few_seasons)
            shooting_vizzes.append(viz)
            
        # plot passing vizzes
        total_choices = ["Total - Passes Completed", "Total - Passes Attempted", "Total - Pass Completion %", "Total - Total Passes Distance", "Total - Progessive Passes Distance", "Total Passes Stack"]
        short_choices = ["Short - Passes Completed", "Short - Passes Attempted", "Short - Pass Completion %"]
        medium_choices = ["Medium - Passes Completed", "Medium - Passes Attempted", "Medium - Pass Completion %"]
        long_choices = ["Long - Passes Completed", "Long - Passes Attempted", "Long - Pass Completion %"]
        other_choices = ["Assists", "xA", "A-xA", "Key Passes", "Final Third Passes", "Passes into Penalty Area", "Crosses into Penalty Area", "Progressive Passes"]
        for choice in total_choices:
            viz = compare_passing_stats_players(player_A_passing_set, player_B_passing_set, comparison=choice, last_few_seasons=last_few_seasons)
            passing_vizzes.append(viz)
        for choice in short_choices:
            viz = compare_passing_stats_players(player_A_passing_set, player_B_passing_set, comparison=choice, last_few_seasons=last_few_seasons)
            passing_vizzes.append(viz)
        for choice in medium_choices:
            viz = compare_passing_stats_players(player_A_passing_set, player_B_passing_set, comparison=choice, last_few_seasons=last_few_seasons)
            passing_vizzes.append(viz)
        for choice in long_choices:
            viz = compare_passing_stats_players(player_A_passing_set, player_B_passing_set, comparison=choice, last_few_seasons=last_few_seasons)
            passing_vizzes.append(viz)
        for choice in other_choices:
            viz = compare_passing_stats_players(player_A_passing_set, player_B_passing_set, comparison=choice, last_few_seasons=last_few_seasons)
            passing_vizzes.append(viz)
        
        # plot defensive actions vizzes
        tackles_choices = ["Tackles - Tackles", "Tackles - Tackles Won", "Tackles - Def 3rd", "Tackles - Mid 3rd", "Tackles - Att 3rd", "Tackles Area Stack"]
        vs_dribbles_choices = ["Vs Dribbles - Dribblers Tackled", "Vs Dribbles - Tackle Attempt Against Dribblers", "Vs Dribbles - Tackles Against Dribblers %", "Vs Dribbles - Dribbled Past", "Tackle Attempts Against Dribblers Stack"]
        pressures_choices = ["Pressures - Press Attempts", "Pressures - Press Successes", "Pressures - Press Success %", "Pressures Stack", "Pressures - Press in Def 3rd", "Pressures - Press in Mid 3rd", "Pressures - Press in Att 3rd", "Pressures Area Stack"]
        blocks_choices = ["Blocks - Blocks Made", "Blocks - Shots Blocked", "Blocks - Shots on Target Blocked", "Blocks - Passes Blocked"]
        other_choices = ["Interceptions", "Tackles + Interceptions", "Clearences", "Errors Leading to Opponent's Shots"]
        for choice in tackles_choices:
            viz = compare_def_acts_stats_players(player_A_def_acts_set, player_B_def_acts_set, comparison=choice, last_few_seasons=last_few_seasons)
            def_acts_vizzes.append(viz)
        for choice in vs_dribbles_choices:
            viz = compare_def_acts_stats_players(player_A_def_acts_set, player_B_def_acts_set, comparison=choice, last_few_seasons=last_few_seasons)
            def_acts_vizzes.append(viz)
        for choice in pressures_choices:
            viz = compare_def_acts_stats_players(player_A_def_acts_set, player_B_def_acts_set, comparison=choice, last_few_seasons=last_few_seasons)
            def_acts_vizzes.append(viz)
        for choice in blocks_choices:
            viz = compare_def_acts_stats_players(player_A_def_acts_set, player_B_def_acts_set, comparison=choice, last_few_seasons=last_few_seasons)
            def_acts_vizzes.append(viz)
        for choice in other_choices:
            viz = compare_def_acts_stats_players(player_A_def_acts_set, player_B_def_acts_set, comparison=choice, last_few_seasons=last_few_seasons)
            def_acts_vizzes.append(viz)
    
    return render(request, 'dashboard/compare.html', {
        "std_stats_vizzes": std_stats_vizzes,
        "shooting_vizzes": shooting_vizzes,
        "passing_vizzes": passing_vizzes,
        "def_acts_vizzes": def_acts_vizzes,
        "player_1": player_1_name.replace('-', ' '),
        "player_2": player_2_name.replace('-', ' '),
    })
    

# API
def database(request):
    data = {}
    for kv_comp, teams in DB.items():
        data[kv_comp[1]] = {}
        for kv_team, players in teams.items():
            data[kv_comp[1]][kv_team[1]] = []
            for id, player in players:
                data[kv_comp[1]][kv_team[1]].append(player)
    return JsonResponse(data, safe=False)
