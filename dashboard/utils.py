import numpy as np
import pandas as pd
import bs4
import requests
import matplotlib.pyplot as plt
import io
import base64


def get_html_document(url):
    # request for HTML document of given url
    response = requests.get(url)
    # response will be provided in JSON format
    return response.text


def scrap_league(league_id, league_name):
  league_url = f'https://fbref.com/en/comps/{league_id}/{league_name}-Stats'
  html_doc = get_html_document(league_url)
  soup = bs4.BeautifulSoup(html_doc, 'html.parser')
  lg_table_soup = soup.find_all('table')[0]
  return lg_table_soup


def scrap_team(team_id, team_name):
  team_url = f'https://fbref.com/en/squads/{team_id}/{team_name}-Stats'
  html_doc = get_html_document(team_url)
  soup = bs4.BeautifulSoup(html_doc, 'html.parser')
  return soup


def scrap_player(player_id, player_name):
  player_url = f'https://fbref.com/en/players/{player_id}/{player_name}'
  # scrape the html content
  html_doc = get_html_document(player_url)
  soup = bs4.BeautifulSoup(html_doc, 'html.parser')
  return soup


def get_player_table(player_soup, table_category='all_stats_standard'):
  # find tag with specified id
  html_std_stats = player_soup.find(id=table_category)
  # remove <tfoot> and its children
  for tfoot in player_soup.find_all('tfoot'):
    tfoot.decompose()
  # get the table
  table = pd.read_html(str(html_std_stats))
  return table[0]


"""
    STANDARD STATISTICS
"""

def clean_standard_stats_table(raw_standard_stats_table):
  """ Remove the multi-index """
  """ Column name ('Playing Time', 'MP') becomes ('Playing Time - MP') """
  # Drop Per 90 Minutes first index columns
  raw_standard_stats_table.drop(['Per 90 Minutes'], axis=1, level=0, inplace=True)

  # Change the column structure to make it just 1 level
  for col in raw_standard_stats_table.columns:
    if 'unnamed' in col[0].lower():
      continue
    new_colname = col[0] + ' - ' + col[1]
    raw_standard_stats_table.rename(columns={col[1]: new_colname}, inplace=True, level=1)
  raw_standard_stats_table = raw_standard_stats_table.droplevel(level=0, axis=1)

  # Drop mathces column and 
  raw_standard_stats_table = raw_standard_stats_table.drop(["Matches", "Squad", "Country", "Comp", "LgRank"], axis=1)
  # # Drop NaN values
  # raw_standard_stats_table = raw_standard_stats_table.dropna()
  
  # Convert string values to numeric
  for col in raw_standard_stats_table.columns:
    if col in ["Season"]:
      continue
    raw_standard_stats_table[col] = pd.to_numeric(raw_standard_stats_table[col], errors='coerce', downcast='integer')

  # Group by and Aggregate
  standard_stats_table = raw_standard_stats_table.groupby(["Season"]).aggregate('sum')
  standard_stats_table.reset_index(inplace=True)
  standard_stats_table.set_index("Season", inplace=True)
  del raw_standard_stats_table
  
  return standard_stats_table


def compare_standard_stats_players(player_A_set: tuple, player_B_set: tuple, comparison='Minutes Played', last_few_seasons=None):
  """
    player_A_set: tuple of (player_name of player A, table of player A)
    Comparison options:
    - 'Time Playing' Comparisons: ["Minutes Played", "Starts", "Matches Played", "90s", "Starts Stack"]
    - 'Expected' Comparisons: ["xG", "npxG", "xA", "npxG+xA"]
  """
  # initialize category and comparison
  if comparison in ["Matches Played", "Starts", "Minutes Played", "90s", "Starts Stack"]:
    category = "Playing Time"
  elif comparison in ["xG",	"npxG",	"xA", "npxG+xA"]:
    category = "Expected"
  else:
    print("Available 'Time Playing' Comparisons:", ["Minutes Played", "Starts", "Matches Played", "90s", "Starts Stack"])
    print("Available 'Expected' Comparisons:", ["xG", "npxG", "xA", "npxG+xA"])
    print("Your Comparison Option:", comparison)
    return

  # unpack the tuple
  player_A, table_A = player_A_set
  player_B, table_B = player_B_set
  table_A = table_A.copy()
  table_B = table_B.copy()

  # take subset of table with chosen category in the column name while also removing the first index name
  assert (table_A.columns == table_B.columns).all()
  for col in table_A.columns:
    if category in col:
      table_A.rename(columns={col: col.replace(f"{category} - ", "")}, inplace=True)
      table_B.rename(columns={col: col.replace(f"{category} - ", "")}, inplace=True)
      continue
    table_A.drop(col, axis=1, inplace=True)
    table_B.drop(col, axis=1, inplace=True)
  
  # set axis for season length
  X_axis_A = np.arange(len(table_A.index))
  X_axis_B = np.arange(len(table_B.index))

  # get the fewest number of seasons recorded between two players to get similar comparisons
  season_len = len(X_axis_A) if len(X_axis_A) <= len(X_axis_B) else len(X_axis_B)
  X_axis = np.arange(season_len)

  # cut the table rows
  table_A = table_A[-season_len:].copy()
  table_B = table_B[-season_len:].copy()

  # expected metrics only recorded 5 seasons prior (since 2017-2018, code is created at April, 2022)
  if category == "Expected":
    table_A = table_A[-5:].copy()
    table_B = table_B[-5:].copy()
    X_axis = np.arange(len(table_A.index))
  
  # if the number of last few seasons is provided
  if last_few_seasons != None:
    if not isinstance(last_few_seasons, int):
      print("Please provide integer to specify last few seasons")
      return
    table_A = table_A[-last_few_seasons:].copy()
    table_B = table_B[-last_few_seasons:].copy()
    X_axis = np.arange(len(table_A.index))

  # initialize figure
  plt.switch_backend('AGG')
  plt.figure(figsize=(10, 6))

  # get the rows where the seasons are recorded for both players
  index = table_A.index
  plt.xticks(X_axis, index, rotation=30, fontsize=12)
  plt.xlabel("Seasons")

  # Playing Time Sections
  if comparison == "Minutes Played":
    plt.bar(X_axis - 0.2, table_A['Min'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Min'], width = 0.4, label = player_B)
    plt.ylabel("Minutes Played", size=12)
    plt.yticks(fontsize=12)
    plt.title("Minutes Played per Season", size=18)

  elif comparison == "Starts":
    plt.bar(X_axis - 0.2, table_A['Starts'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Starts'], width = 0.4, label = player_B)
    plt.ylabel("Starts", size=12)
    plt.yticks(fontsize=12)
    plt.title("Starts per Season", size=18)

  elif comparison == "Matches Played":
    plt.bar(X_axis - 0.2, table_A['MP'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['MP'], width = 0.4, label = player_B)
    plt.ylabel("Matches Played", size=12)
    plt.yticks(fontsize=12)
    plt.title("Matches Played per Season", size=18)

  elif comparison == "90s":
    plt.bar(X_axis - 0.2, table_A['90s'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['90s'], width = 0.4, label = player_B)
    plt.ylabel("Minutes Played per 90s", size=12)
    plt.yticks(fontsize=12)
    plt.title("Minutes Played per 90s per Season", size=18)

  elif comparison == "Starts Stack":
    table_A["Non-Starter"] = table_A["MP"] - table_A["Starts"]
    table_B["Non-Starter"] = table_B["MP"] - table_B["Starts"]
    plt.bar(X_axis - 0.2, table_A['Starts'], width = 0.4, label = player_A + ' Starter')
    plt.bar(X_axis - 0.2, table_A['Non-Starter'], bottom = table_A["Starts"], width = 0.4, label = player_A + ' Non-Starter')
    plt.bar(X_axis + 0.2, table_B['Starts'], width = 0.4, label = player_B + ' Starter')
    plt.bar(X_axis + 0.2, table_B['Non-Starter'], bottom = table_B["Starts"], width = 0.4, label = player_B + ' Non-Starter')
    plt.ylabel("Matches Played per Season", size=12)
    plt.yticks(fontsize=12)
    plt.title("Matches Played per Season", size=18)
    # setting y ticks
    max_y = max(table_A['MP'].max(), table_B['MP'].max())
    y_ticks = np.arange(0, max_y+5, 5)
    plt.yticks(y_ticks)
  
  # Expected Sections
  elif comparison == "xG":
    plt.bar(X_axis - 0.2, table_A['xG'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['xG'], width = 0.4, label = player_B)
    plt.ylabel("Expected Goals", size=12)
    plt.yticks(fontsize=12)
    plt.title("Expected Goals per Season", size=18)

  elif comparison == "npxG":
    plt.bar(X_axis - 0.2, table_A['npxG'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['npxG'], width = 0.4, label = player_B)
    plt.ylabel("non-penalty Expected Goals", size=12)
    plt.yticks(fontsize=12)
    plt.title("non-penalty Expected Goals per Season", size=18)

  elif comparison == "xA":
    plt.bar(X_axis - 0.2, table_A['xA'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['xA'], width = 0.4, label = player_B)
    plt.ylabel("Expected Assists", size=12)
    plt.yticks(fontsize=12)
    plt.title("Expected Assists per Season", size=18)

  elif comparison == "npxG+xA":
    plt.bar(X_axis - 0.2, table_A['npxG+xA'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['npxG+xA'], width = 0.4, label = player_B)
    plt.ylabel("Expected non-penalty Goals + Assists", size=12)
    plt.yticks(fontsize=12)
    plt.title("Expected non-penalty Goals + Assists per Season", size=18)
  
  plt.legend(loc='best', framealpha=0.5)
  
  # adjusts the size of the chart to the size of the figure
  plt.tight_layout()
  
  # get the bytes data
  chart = get_graph()
  
  return chart


"""
    SHOOTING STATISTICS
"""

def clean_shooting_stats_table(raw_shooting_stats_table):
  # Change the column structure to make it just 1 level
  for col in raw_shooting_stats_table.columns:
    if 'unnamed' in col[0].lower():
      continue
    new_colname = col[0] + ' - ' + col[1]
    raw_shooting_stats_table.rename(columns={col[1]: new_colname}, inplace=True, level=1)
  raw_shooting_stats_table = raw_shooting_stats_table.droplevel(level=0, axis=1)

  # Drop mathces column and 
  raw_shooting_stats_table = raw_shooting_stats_table.drop(["Matches", "Squad", "Country", "Comp", "LgRank"], axis=1)
  # # Drop NaN values
  # raw_shooting_stats_table = raw_shooting_stats_table.dropna()
  
  # Convert string values to numeric
  for col in raw_shooting_stats_table.columns:
    if col in ["Season"]:
      continue
    raw_shooting_stats_table[col] = pd.to_numeric(raw_shooting_stats_table[col], errors='coerce', downcast='integer')

  # Group by and Aggregate
  shooting_stats_table = raw_shooting_stats_table.groupby(["Season"]).aggregate('sum')
  shooting_stats_table.reset_index(inplace=True)
  shooting_stats_table.set_index("Season", inplace=True)
  del raw_shooting_stats_table
  
  return shooting_stats_table


def compare_shooting_stats_players(player_A_set:tuple, player_B_set:tuple, comparison:str='Goals', last_few_seasons:int=None):
  """
    player_A_set: tuple of (player_name of player A, table of player A)
    Comparison options:
    - 'Standard' Comparisons: ["Goals", "Shoot", "SoT", "SoT%", "Sh/90", "SoT/90", "G/Sh", "G/SoT", "Dist", "Goals Stack"]
    - 'Expected' Comparisons: ["xG", "npxG", "npxG/Sh", "G-xG", "np:G-xG"]
  """
  # initialize category and comparison
  if comparison in ["Goals", "Shoot", "SoT", "SoT%", "Sh/90", "SoT/90", "G/Sh", "G/SoT", "Dist", "Goals Stack"]:
    category = "Standard"
  elif comparison in ["xG", "npxG", "npxG/Sh", "G-xG", "np:G-xG"]:
    category = "Expected"
  else:
    print("Available 'Time Playing' Comparisons:", ["Gls", "Shoot", "SoT", "SoT%", "Sh/90", "SoT/90", "G/Sh", "G/SoT", "Dist", "Goals Stack"])
    print("Available 'Expected' Comparisons:", ["xG", "npxG", "npxG/Sh", "G-xG", "np:G-xG"])
    print("Your Comparison Option:", comparison)
    return

  # unpack the tuple
  player_A, table_A = player_A_set
  player_B, table_B = player_B_set
  table_A = table_A.copy()
  table_B = table_B.copy()

  # take subset of table with chosen category in the column name while also removing the first index name
  assert (table_A.columns == table_B.columns).all()
  for col in table_A.columns:
    if category in col:
      table_A.rename(columns={col: col.replace(f"{category} - ", "")}, inplace=True)
      table_B.rename(columns={col: col.replace(f"{category} - ", "")}, inplace=True)
      continue
    table_A.drop(col, axis=1, inplace=True)
    table_B.drop(col, axis=1, inplace=True)
  
  # set axis for season length
  X_axis_A = np.arange(len(table_A.index))
  X_axis_B = np.arange(len(table_B.index))

  # get the fewest number of seasons recorded between two players to get similar comparisons
  season_len = len(X_axis_A) if len(X_axis_A) <= len(X_axis_B) else len(X_axis_B)
  X_axis = np.arange(season_len)

  # cut the table rows
  table_A = table_A[-season_len:].copy()
  table_B = table_B[-season_len:].copy()

  # expected metrics only recorded 5 seasons prior (since 2017-2018, code is created at April, 2022)
  if category == "Expected":
    table_A = table_A[-5:].copy()
    table_B = table_B[-5:].copy()
    X_axis = np.arange(len(table_A.index))
  
  # if the number of last few seasons is provided
  if last_few_seasons != None:
    if not isinstance(last_few_seasons, int):
      print("Please provide integer to specify last few seasons")
      return
    if last_few_seasons > 0:
      print("Please provide number of seasons more than 0")
      return
    table_A = table_A[-last_few_seasons:].copy()
    table_B = table_B[-last_few_seasons:].copy()
    X_axis = np.arange(len(table_A.index))

  # initialize figure
  plt.switch_backend('AGG')
  plt.figure(figsize=(10, 6))

  # get the rows where the seasons are recorded for both players
  index = table_A.index
  plt.xticks(X_axis, index, rotation=30, fontsize=12)
  plt.xlabel("Seasons")

  # Standard Sections
  if comparison == "Goals":
    plt.bar(X_axis - 0.2, table_A['Gls'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Gls'], width = 0.4, label = player_B)
    plt.ylabel("Goals Scored", size=12)
    plt.yticks(fontsize=12)
    plt.title("Goals Scored per Season", size=18)

  elif comparison == "Shoot":
    plt.bar(X_axis - 0.2, table_A['Sh'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Sh'], width = 0.4, label = player_B)
    plt.ylabel("Shots", size=12)
    plt.yticks(fontsize=12)
    plt.title("Shots per Season", size=18)

  elif comparison == "SoT":
    plt.bar(X_axis - 0.2, table_A["SoT"], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B["SoT"], width = 0.4, label = player_B)
    plt.ylabel("Shots on Target", size=12)
    plt.yticks(fontsize=12)
    plt.title("Shots on Target per Season", size=18)

  elif comparison == "SoT%":
    plt.bar(X_axis - 0.2, table_A["SoT%"], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B["SoT%"], width = 0.4, label = player_B)
    plt.ylabel("Shots on Target Percentage", size=12)
    plt.yticks(fontsize=12)
    plt.title("Shots on Target Percentage per Season", size=18)

  elif comparison == "Sh/90":
    plt.bar(X_axis - 0.2, table_A["Sh/90"], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B["Sh/90"], width = 0.4, label = player_B)
    plt.ylabel("Shots on Target per 90s", size=12)
    plt.yticks(fontsize=12)
    plt.title("Shots on Target per 90s per Season", size=18)

  elif comparison == "SoT/90":
    plt.bar(X_axis - 0.2, table_A["SoT/90"], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B["SoT/90"], width = 0.4, label = player_B)
    plt.ylabel("Shots on Target per 90s", size=12)
    plt.yticks(fontsize=12)
    plt.title("Shots on Target per 90s per Season", size=18)

  elif comparison == "G/Sh":
    plt.bar(X_axis - 0.2, table_A["G/Sh"], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B["G/Sh"], width = 0.4, label = player_B)
    plt.ylabel("Goals per Shots", size=12)
    plt.yticks(fontsize=12)
    plt.title("Goals per Shots per Season", size=18)

  elif comparison == "G/SoT":
    plt.bar(X_axis - 0.2, table_A["G/SoT"], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B["G/SoT"], width = 0.4, label = player_B)
    plt.ylabel("Goals per Shots on Target", size=12)
    plt.yticks(fontsize=12)
    plt.title("Goals per Shots on Target per Season", size=18)

  elif comparison == "Dist":
    plt.bar(X_axis - 0.2, table_A["Dist"], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B["Dist"], width = 0.4, label = player_B)
    plt.ylabel("Average Distance of Shots Taken from Goal per 90s", size=12)
    plt.yticks(fontsize=12)
    plt.title("Average Distance of Shots Taken from Goal per 90s per Season", size=18)

  elif comparison == "Goals Stack":
    table_A["Non-Penalty-Goals"] = table_A["Gls"] - table_A["PK"]
    table_B["Non-Penalty-Goals"] = table_B["Gls"] - table_B["PK"]
    plt.bar(X_axis - 0.2, table_A['Non-Penalty-Goals'], width = 0.4, label = player_A + ' Non-Penalty Goals')
    plt.bar(X_axis - 0.2, table_A['PK'], bottom = table_A["Non-Penalty-Goals"], width = 0.4, label = player_A + ' Penalty Goals')
    plt.bar(X_axis + 0.2, table_B['Non-Penalty-Goals'], width = 0.4, label = player_B + ' Non-Penalty Goals')
    plt.bar(X_axis + 0.2, table_B['PK'], bottom = table_B["Non-Penalty-Goals"], width = 0.4, label = player_B + ' Penalty Goals')
    plt.ylabel("Goals Scored per Season", size=12)
    plt.yticks(fontsize=12)
    plt.title("Goals Scored per Season", size=18)
    # setting y ticks
    max_y = max(table_A['Gls'].max(), table_B['Gls'].max())
    y_ticks = np.arange(0, max_y+5, 5)
    plt.yticks(y_ticks)
  
  # Expected Sections
  elif comparison == "xG":
    plt.bar(X_axis - 0.2, table_A['xG'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['xG'], width = 0.4, label = player_B)
    plt.ylabel("Expected Goals", size=12)
    plt.yticks(fontsize=12)
    plt.title("Expected Goals per Season", size=18)

  elif comparison == "npxG":
    plt.bar(X_axis - 0.2, table_A['npxG'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['npxG'], width = 0.4, label = player_B)
    plt.ylabel("non-penalty Expected Goals", size=12)
    plt.yticks(fontsize=12)
    plt.title("non-penalty Expected Goals per Season", size=18)

  elif comparison == "npxG/Sh":
    plt.bar(X_axis - 0.2, table_A['npxG/Sh'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['npxG/Sh'], width = 0.4, label = player_B)
    plt.ylabel("Expected non-penalty Goals per Shots", size=12)
    plt.yticks(fontsize=12)
    plt.title("Expected non-penalty Goals per Shots per Season", size=18)

  elif comparison == "G-xG":
    plt.bar(X_axis - 0.2, table_A["G-xG"], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B["G-xG"], width = 0.4, label = player_B)
    plt.ylabel("Goals-xG", size=12)
    plt.yticks(fontsize=12)
    plt.title("Goals-xG per Season", size=18)

  elif comparison == "np:G-xG":
    plt.bar(X_axis - 0.2, table_A["np:G-xG"], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B["np:G-xG"], width = 0.4, label = player_B)
    plt.ylabel("npG-npxG", size=12)
    plt.yticks(fontsize=12)
    plt.title("Non Penalty Goals - Non Penalty Expected Goals per Season", size=18)
  
  plt.legend(loc='best', framealpha=0.5)
  
  # adjusts the size of the chart to the size of the figure
  plt.tight_layout()
  
  # get the bytes data
  chart = get_graph()
  
  return chart


"""
  PASSING
"""

def clean_passing_stats_table(raw_passing_stats_table):
  # Change the column structure to make it just 1 level
  for col in raw_passing_stats_table.columns:
    if 'unnamed' in col[0].lower():
      continue
    new_colname = col[0] + ' - ' + col[1]
    raw_passing_stats_table[('unnamed', new_colname)] = raw_passing_stats_table[col]
    raw_passing_stats_table.drop(col, inplace=True, axis=1)
  raw_passing_stats_table = raw_passing_stats_table.droplevel(level=0, axis=1)

  # Drop mathces column and 
  raw_passing_stats_table = raw_passing_stats_table.drop(["Matches", "Squad", "Country", "Comp", "LgRank"], axis=1)
  # # Drop NaN values
  # raw_passing_stats_table = raw_passing_stats_table.dropna()
  
  # Convert string values to numeric
  for col in raw_passing_stats_table.columns:
    if col in ["Season"]:
      continue
    raw_passing_stats_table[col] = pd.to_numeric(raw_passing_stats_table[col], errors='coerce', downcast='float')
    # raw_passing_stats_table[col] = raw_passing_stats_table[col].apply(pd.to_numeric, errors='coerce', downcast='float')

  # Group by and Aggregate
  passing_stats_table = raw_passing_stats_table.groupby(["Season"]).aggregate('sum')
  passing_stats_table.reset_index(inplace=True)
  passing_stats_table.set_index("Season", inplace=True)
  del raw_passing_stats_table
  
  return passing_stats_table


def compare_passing_stats_players(player_A_set:tuple, player_B_set:tuple, comparison:str=None, last_few_seasons:int=None):
  """
    player_A_set: tuple of (player_name of player A, table of player A)
    Comparison options:
    - 'Total' Comparisons: ["Total - Passes Completed", "Total - Passes Attempted", "Total - Pass Completion %", "Total - Total Passes Distance", "Total - Progessive Passes Distance"]
    - 'Short' Comparisons: ["Short - Passes Completed", "Short - Passes Attempted", "Short - Pass Completion %"]
    - 'Medium' Comparisons: ["Medium - Passes Completed", "Medium - Passes Attempted", "Medium - Pass Completion %"]
    - 'Long' Comparisons: ["Long - Passes Completed", "Long - Passes Attempted", "Long - Pass Completion %"]
    - 'unnamed' Comparisons: ["Assists", "xA", "A-xA", "Key Passes", "Final Third Passes", "Passes into Penalty Area", "Crosses into Penalty Area", "Progressive Passes"]
  """
  # initialize category and comparison
  if comparison not in ["Total - Passes Completed", "Total - Passes Attempted", "Total - Pass Completion %", "Total - Total Passes Distance", "Total - Progessive Passes Distance", "Total Passes Stack"] + ["Short - Passes Completed", "Short - Passes Attempted", "Short - Pass Completion %"] + ["Medium - Passes Completed", "Medium - Passes Attempted", "Medium - Pass Completion %"] + ["Long - Passes Completed", "Long - Passes Attempted", "Long - Pass Completion %"] + ["Assists", "xA", "A-xA", "Key Passes", "Final Third Passes", "Passes into Penalty Area", "Crosses into Penalty Area", "Progressive Passes"]:
    print("Available 'Total' Comparisons:", ["Total - Passes Completed", "Total - Passes Attempted", "Total - Pass Completion %", "Total - Total Passes Distance", "Total - Progessive Passes Distance"])
    print("Available 'Short' Comparisons:", ["Short - Passes Completed", "Short - Passes Attempted", "Short - Pass Completion %"])
    print("Available 'Medium' Comparisons:", ["Medium - Passes Completed", "Medium - Passes Attempted", "Medium - Pass Completion %"])
    print("Available 'Long' Comparisons:", ["Long - Passes Completed", "Long - Passes Attempted", "Long - Pass Completion %"])
    print("Available 'Other' Comparisons:", ["Assists", "xA", "A-xA", "Key Passes", "Final Third Passes", "Passes into Penalty Area", "Crosses into Penalty Area", "Progressive Passes"])
    print("Your Comparison Option:", comparison)
    return

  # unpack the tuple
  player_A, table_A = player_A_set
  player_B, table_B = player_B_set
  table_A = table_A.copy()
  table_B = table_B.copy()
  
  # set axis for season length
  X_axis_A = np.arange(len(table_A.index))
  X_axis_B = np.arange(len(table_B.index))

  # get the fewest number of seasons recorded between two players to get similar comparisons
  season_len = len(X_axis_A) if len(X_axis_A) <= len(X_axis_B) else len(X_axis_B)
  X_axis = np.arange(season_len)

  # cut the table rows
  table_A = table_A[-season_len:].copy()
  table_B = table_B[-season_len:].copy()

  # all the metrics except assist only recorded 5 seasons prior (since 2017-2018, code is created at Mei, 2022)
  table_A = table_A[-5:].copy()
  table_B = table_B[-5:].copy()
  X_axis = np.arange(len(table_A.index))
  
  # if the number of last few seasons is provided
  if last_few_seasons != None:
    if not isinstance(last_few_seasons, int):
      print("Please provide integer to specify last few seasons")
      return
    table_A = table_A[-last_few_seasons:].copy()
    table_B = table_B[-last_few_seasons:].copy()
    X_axis = np.arange(len(table_A.index))

  # initialize figure
  plt.switch_backend('AGG')
  plt.figure(figsize=(10, 6))

  # get the rows where the seasons are recorded for both players
  index = table_A.index
  plt.xticks(X_axis, index, rotation=30, fontsize=12)
  plt.xlabel("Seasons", size=12)

  # Total Sections
  if comparison == "Total - Passes Completed":
    plt.bar(X_axis - 0.2, table_A['Total - Cmp'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Total - Cmp'], width = 0.4, label = player_B)
    plt.ylabel("Total Passes Completed", size=12)
    plt.yticks(fontsize=12)
    plt.title("Total Passes Completed per Season", size=18)

  elif comparison == "Total - Passes Attempted":
    plt.bar(X_axis - 0.2, table_A['Total - Att'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Total - Att'], width = 0.4, label = player_B)
    plt.ylabel("Total Passes Attempted", size=12)
    plt.yticks(fontsize=12)
    plt.title("Total Passes Attempted per Season", size=18)

  elif comparison == "Total - Pass Completion %":
    plt.bar(X_axis - 0.2, table_A['Total - Cmp%'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Total - Cmp%'], width = 0.4, label = player_B)
    plt.ylabel("Pass Completion %", size=12)
    plt.yticks(fontsize=12)
    plt.title("Pass Completion % per Season", size=18)
    
  elif comparison == "Total - Total Passes Distance":
    plt.bar(X_axis - 0.2, table_A['Total - TotDist'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Total - TotDist'], width = 0.4, label = player_B)
    plt.ylabel("Total Passes Distance (in yards)", size=12)
    plt.yticks(fontsize=12)
    plt.title("Passes Passes Distance (in yards) per Season", size=18)
    
  elif comparison == "Total - Progessive Passes Distance":
    plt.bar(X_axis - 0.2, table_A['Total - PrgDist'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Total - PrgDist'], width = 0.4, label = player_B)
    plt.ylabel("Progessive Passes Distance (in yards)", size=12)
    plt.yticks(fontsize=12)
    plt.title("Progessive Passes Distance (in yards) per Season", size=18)

  elif comparison == "Total Passes Stack":
    table_A["Total-Failed-Passes"] = table_A["Total - Att"] - table_A["Total - Cmp"]
    table_B["Total-Failed-Passes"] = table_B["Total - Att"] - table_B["Total - Cmp"]
    plt.bar(X_axis - 0.2, table_A['Total - Cmp'], width = 0.4, label = player_A + ' Total Completed Passes')
    plt.bar(X_axis - 0.2, table_A['Total-Failed-Passes'], bottom = table_A["Total - Cmp"], width = 0.4, label = player_A + ' Total Failed Passes')
    plt.bar(X_axis + 0.2, table_B['Total - Cmp'], width = 0.4, label = player_B + ' Total Completed Passes')
    plt.bar(X_axis + 0.2, table_B['Total-Failed-Passes'], bottom = table_B["Total - Cmp"], width = 0.4, label = player_B + ' Total Failed Passes')
    plt.ylabel("Total Passes Attempted", size=12)
    plt.yticks(fontsize=12)
    plt.title("Total Passes Attempted per Season", size=18)
    # setting y ticks
    max_y = max(table_A['Total - Att'].max(), table_B['Total - Att'].max())
    y_ticks = np.arange(0, max_y+50, 100)
    plt.yticks(y_ticks)
  
  # Short Sections
  elif comparison == "Short - Passes Completed":
    plt.bar(X_axis - 0.2, table_A['Short - Cmp'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Short - Cmp'], width = 0.4, label = player_B)
    plt.ylabel("Short Passes Completed", size=12)
    plt.yticks(fontsize=12)
    plt.title("Short Passes Completed per Season", size=18)

  elif comparison == "Short - Passes Attempted":
    plt.bar(X_axis - 0.2, table_A['Short - Att'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Short - Att'], width = 0.4, label = player_B)
    plt.ylabel("Short Passes Attempted", size=12)
    plt.yticks(fontsize=12)
    plt.title("Short Passes Attempted per Season", size=18)

  elif comparison == "Short - Pass Completion %":
    plt.bar(X_axis - 0.2, table_A['Short - Cmp%'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Short - Cmp%'], width = 0.4, label = player_B)
    plt.ylabel("Short Pass Completion %", size=12)
    plt.yticks(fontsize=12)
    plt.title("Short Pass Completion % per Season", size=18)
    
  # Medium Sections
  elif comparison == "Medium - Passes Completed":
    plt.bar(X_axis - 0.2, table_A['Medium - Cmp'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Medium - Cmp'], width = 0.4, label = player_B)
    plt.ylabel("Medium Passes Completed", size=12)
    plt.yticks(fontsize=12)
    plt.title("Medium Passes Completed per Season", size=18)

  elif comparison == "Medium - Passes Attempted":
    plt.bar(X_axis - 0.2, table_A['Medium - Att'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Medium - Att'], width = 0.4, label = player_B)
    plt.ylabel("Medium Passes Attempted", size=12)
    plt.yticks(fontsize=12)
    plt.title("Medium Passes Attempted per Season", size=18)

  elif comparison == "Medium - Pass Completion %":
    plt.bar(X_axis - 0.2, table_A['Medium - Cmp%'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Medium - Cmp%'], width = 0.4, label = player_B)
    plt.ylabel("Medium Pass Completion %", size=12)
    plt.yticks(fontsize=12)
    plt.title("Medium Pass Completion % per Season", size=18)
    
  # Long Sections
  elif comparison == "Long - Passes Completed":
    plt.bar(X_axis - 0.2, table_A['Long - Cmp'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Long - Cmp'], width = 0.4, label = player_B)
    plt.ylabel("Long Passes Completed", size=12)
    plt.yticks(fontsize=12)
    plt.title("Long Passes Completed per Season", size=18)

  elif comparison == "Long - Passes Attempted":
    plt.bar(X_axis - 0.2, table_A['Long - Att'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Long - Att'], width = 0.4, label = player_B)
    plt.ylabel("Long Passes Attempted", size=12)
    plt.yticks(fontsize=12)
    plt.title("Long Passes Attempted per Season", size=18)

  elif comparison == "Long - Pass Completion %":
    plt.bar(X_axis - 0.2, table_A['Long - Cmp%'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Long - Cmp%'], width = 0.4, label = player_B)
    plt.ylabel("Long Pass Completion %", size=12)
    plt.yticks(fontsize=12)
    plt.title("Long Pass Completion % per Season", size=18)
  
  # unnamed sections
  elif comparison == "Assists":
    plt.bar(X_axis - 0.2, table_A['Ast'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Ast'], width = 0.4, label = player_B)
    plt.ylabel("Assists", size=12)
    plt.yticks(fontsize=12)
    plt.title("Assists per Season", size=18)
    
  elif comparison == "xA":
    plt.bar(X_axis - 0.2, table_A['xA'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['xA'], width = 0.4, label = player_B)
    plt.ylabel("Expected Assists", size=12)
    plt.yticks(fontsize=12)
    plt.title("Expected Assists per Season", size=18)
    
  elif comparison == "A-xA":
    plt.bar(X_axis - 0.2, table_A['A-xA'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['A-xA'], width = 0.4, label = player_B)
    plt.ylabel("Assists - Expected Assists", size=12)
    plt.yticks(fontsize=12)
    plt.title("Assists - Expected Assists per Season", size=18)
    
  elif comparison == "Key Passes":
    plt.bar(X_axis - 0.2, table_A['KP'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['KP'], width = 0.4, label = player_B)
    plt.ylabel("Key Passes", size=12)
    plt.yticks(fontsize=12)
    plt.title("Key Passes per Season", size=18)
    
  elif comparison == "Final Third Passes":
    plt.bar(X_axis - 0.2, table_A['1/3'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['1/3'], width = 0.4, label = player_B)
    plt.ylabel("Passes into Final Third", size=12)
    plt.yticks(fontsize=12)
    plt.title("Passes into Final Third per Season", size=18)
    
  elif comparison == "Passes into Penalty Area":
    plt.bar(X_axis - 0.2, table_A['PPA'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['PPA'], width = 0.4, label = player_B)
    plt.ylabel("Passes into Penalty Area", size=12)
    plt.yticks(fontsize=12)
    plt.title("Passes into Penalty Area per Season", size=18)
    
  elif comparison == "Crosses into Penalty Area":
    plt.bar(X_axis - 0.2, table_A['CrsPA'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['CrsPA'], width = 0.4, label = player_B)
    plt.ylabel("Crosses into Penalty Area", size=12)
    plt.yticks(fontsize=12)
    plt.title("Crosses into Penalty Area per Season", size=18)
    
  elif comparison == "Progressive Passes":
    plt.bar(X_axis - 0.2, table_A['Prog'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Prog'], width = 0.4, label = player_B)
    plt.ylabel("Progressive Passes", size=12)
    plt.yticks(fontsize=12)
    plt.title("Progressive Passes per Season", size=18)
  
  plt.legend(loc='best', framealpha=0.5)
  
  # adjusts the size of the chart to the size of the figure
  plt.tight_layout()
  
  # get the bytes data
  chart = get_graph()
  
  return chart


"""
  DEFENSIVE ACTIONS
"""

def clean_def_acts_stats_table(raw_def_acts_stats_table):
  # Change the column structure to make it just 1 level
  for col in raw_def_acts_stats_table.columns:
    if 'unnamed' in col[0].lower():
      continue
    new_colname = col[0] + ' - ' + col[1]
    raw_def_acts_stats_table[('unnamed', new_colname)] = raw_def_acts_stats_table[col]
    raw_def_acts_stats_table.drop(col, inplace=True, axis=1)
  raw_def_acts_stats_table = raw_def_acts_stats_table.droplevel(level=0, axis=1)

  # Drop mathces column and 
  raw_def_acts_stats_table = raw_def_acts_stats_table.drop(["Matches", "Squad", "Country", "Comp", "LgRank"], axis=1)
  # # Drop NaN values
  # raw_def_acts_stats_table = raw_def_acts_stats_table.dropna()
  
  # Convert string values to numeric
  for col in raw_def_acts_stats_table.columns:
    if col in ["Season"]:
      continue
    raw_def_acts_stats_table[col] = pd.to_numeric(raw_def_acts_stats_table[col], errors='coerce', downcast='float')
    # raw_def_acts_stats_table[col] = raw_def_acts_stats_table[col].apply(pd.to_numeric, errors='coerce', downcast='float')

  # Group by and Aggregate
  def_acts_stats_table = raw_def_acts_stats_table.groupby(["Season"]).aggregate('sum')
  def_acts_stats_table.reset_index(inplace=True)
  def_acts_stats_table.set_index("Season", inplace=True)
  del raw_def_acts_stats_table
  
  return def_acts_stats_table


def compare_def_acts_stats_players(player_A_set:tuple, player_B_set:tuple, comparison:str=None, last_few_seasons:int=None):
  """
    player_A_set: tuple of (player_name of player A, table of player A)
    Comparison options:
    - 'Tackles' Comparisons: ["Tackles - Tackles", "Tackles - Tackles Won", "Tackles - Def 3rd", "Tackles - Mid 3rd", "Tackles - Att 3rd", "Tackles Area Stack"]
    - 'Vs Dribbles' Comparisons: ["Vs Dribbles - Dribblers Tackled", "Vs Dribbles - Tackle Attempt Against Dribblers", "Vs Dribbles - Tackles Against Dribblers %", "Vs Dribbles - Dribbled Past", "Tackle Attempts Against Dribblers Stack"]
    - 'Pressures' Comparisons: ["Pressures - Press Attempts", "Pressures - Press Successes", "Pressures - Press Success %", "Pressures Stack", "Pressures - Press in Def 3rd", "Pressures - Press in Mid 3rd", "Pressures - Press in Att 3rd", "Pressures Area Stack"]
    - 'Blocks' Comparisons: ["Blocks - Blocks Made", "Blocks - Shots Blocked", "Blocks - Shots on Target Blocked", "Blocks - Passes Blocked"]
    - 'Other' Comparisons: ["Interceptions", "Tackles + Interceptions", "Clearences", "Errors Leading to Opponent's Shots"]
  """
  # initialize category and comparison
  if comparison not in ["Tackles - Tackles", "Tackles - Tackles Won", "Tackles - Def 3rd", "Tackles - Mid 3rd", "Tackles - Att 3rd", "Tackles Area Stack"] + ["Vs Dribbles - Dribblers Tackled", "Vs Dribbles - Tackle Attempt Against Dribblers", "Vs Dribbles - Tackles Against Dribblers %", "Vs Dribbles - Dribbled Past", "Tackle Attempts Against Dribblers Stack"] + ["Pressures - Press Attempts", "Pressures - Press Successes", "Pressures - Press Success %", "Pressures Stack", "Pressures - Press in Def 3rd", "Pressures - Press in Mid 3rd", "Pressures - Press in Att 3rd", "Pressures Area Stack"] + ["Blocks - Blocks Made", "Blocks - Shots Blocked", "Blocks - Shots on Target Blocked", "Blocks - Passes Blocked"] + ["Interceptions", "Tackles + Interceptions", "Clearences", "Errors Leading to Opponent's Shots"]:
    print("Available 'Tackles' Comparisons:", ["Tackles - Tackles", "Tackles - Tackles Won", "Tackles - Def 3rd", "Tackles - Mid 3rd", "Tackles - Att 3rd", "Tackles Area Stack"])
    print("Available 'Vs Dribbles' Comparisons:", ["Vs Dribbles - Dribblers Tackled", "Vs Dribbles - Tackle Attempt Against Dribblers", "Vs Dribbles - Tackles Against Dribblers %", "Vs Dribbles - Dribbled Past", "Tackle Attempts Against Dribblers Stack"])
    print("Available 'Pressures' Comparisons:", ["Pressures - Press Attempts", "Pressures - Press Successes", "Pressures - Press Success %", "Pressures Stack", "Pressures - Press in Def 3rd", "Pressures - Press in Mid 3rd", "Pressures - Press in Att 3rd", "Pressures Area Stack"])
    print("Available 'Blocks' Comparisons:", ["Blocks - Blocks Made", "Blocks - Shots Blocked", "Blocks - Shots on Target Blocked", "Blocks - Passes Blocked"])
    print("Available 'Other' Comparisons:", ["Interceptions", "Tackles + Interceptions", "Clearences", "Errors Leading to Opponent's Shots"])
    print("Your Comparison Option:", comparison)
    return

  # unpack the tuple
  player_A, table_A = player_A_set
  player_B, table_B = player_B_set
  table_A = table_A.copy()
  table_B = table_B.copy()
  
  # set axis for season length
  X_axis_A = np.arange(len(table_A.index))
  X_axis_B = np.arange(len(table_B.index))

  # get the fewest number of seasons recorded between two players to get similar comparisons
  season_len = len(X_axis_A) if len(X_axis_A) <= len(X_axis_B) else len(X_axis_B)
  X_axis = np.arange(season_len)

  # cut the table rows
  table_A = table_A[-season_len:].copy()
  table_B = table_B[-season_len:].copy()

  # all the metrics except tackles won and interceptions only recorded 5 seasons prior (since 2017-2018, code is created at Mei, 2022)
  table_A = table_A[-5:].copy()
  table_B = table_B[-5:].copy()
  X_axis = np.arange(len(table_A.index))
  
  # if the number of last few seasons is provided
  if last_few_seasons != None:
    if not isinstance(last_few_seasons, int):
      print("Please provide integer to specify last few seasons")
      return
    table_A = table_A[-last_few_seasons:].copy()
    table_B = table_B[-last_few_seasons:].copy()
    X_axis = np.arange(len(table_A.index))

  # initialize figure
  plt.switch_backend('AGG')
  plt.figure(figsize=(10, 6))

  # get the rows where the seasons are recorded for both players
  index = table_A.index
  plt.xticks(X_axis, index, rotation=30, fontsize=12)
  plt.xlabel("Seasons", size=12)

  # Tackles Sections
  if comparison == "Tackles - Tackles":
    plt.bar(X_axis - 0.2, table_A['Tackles - Tkl'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Tackles - Tkl'], width = 0.4, label = player_B)
    plt.ylabel("Tackles Made", size=12)
    plt.yticks(fontsize=12)
    plt.title("Tackles Made per Season", size=18)

  elif comparison == "Tackles - Tackles Won":
    plt.bar(X_axis - 0.2, table_A['Tackles - TklW'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Tackles - TklW'], width = 0.4, label = player_B)
    plt.ylabel("Tackles Won", size=12)
    plt.yticks(fontsize=12)
    plt.title("Tackles Won per Season", size=18)

  elif comparison == "Tackles - Tackles Won %":
    table_A['Tackles - Tackles Won %'] = (table_A['Tackles - Tackles Won'] / table_A['Tackles - Tackles']) * 100
    table_B['Tackles - Tackles Won %'] = (table_B['Tackles - Tackles Won'] / table_B['Tackles - Tackles']) * 100
    plt.bar(X_axis - 0.2, table_A['Tackles - Tackles Won %'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Tackles - Tackles Won %'], width = 0.4, label = player_B)
    plt.ylabel("Tackles Won %", size=12)
    plt.yticks(fontsize=12)
    plt.title("Tackles Won % per Season", size=18)

  elif comparison == "Tackles - Def 3rd":
    plt.bar(X_axis - 0.2, table_A['Tackles - Def 3rd'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Tackles - Def 3rd'], width = 0.4, label = player_B)
    plt.ylabel("Tackles in Defensive 3rd", size=12)
    plt.yticks(fontsize=12)
    plt.title("Tackles in Defensive 3rd per Season", size=18)
    
  elif comparison == "Tackles - Mid 3rd":
    plt.bar(X_axis - 0.2, table_A['Tackles - Mid 3rd'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Tackles - Mid 3rd'], width = 0.4, label = player_B)
    plt.ylabel("Tackles in Middle 3rd", size=12)
    plt.yticks(fontsize=12)
    plt.title("Tackles in Middle 3rd per Season", size=18)
    
  elif comparison == "Tackles - Att 3rd":
    plt.bar(X_axis - 0.2, table_A['Tackles - Att 3rd'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Tackles - Att 3rd'], width = 0.4, label = player_B)
    plt.ylabel("Tackles in Attacking 3rd", size=12)
    plt.yticks(fontsize=12)
    plt.title("Tackles in Attacking 3rd per Season", size=18)

  elif comparison == "Tackles Area Stack":
    plt.bar(X_axis - 0.2, table_A['Tackles - Def 3rd'], width = 0.4, label = player_A + ' Tackles in Defensive 3rd')
    plt.bar(X_axis - 0.2, table_A['Tackles - Mid 3rd'], bottom = table_A["Tackles - Def 3rd"], width = 0.4, label = player_A + ' Tackles in Middle Third')
    plt.bar(X_axis - 0.2, table_A['Tackles - Att 3rd'], bottom = (table_A["Tackles - Def 3rd"] + table_A["Tackles - Mid 3rd"]), width = 0.4, label = player_A + ' Tackles in Attacking 3rd')
    plt.bar(X_axis + 0.2, table_B['Tackles - Def 3rd'], width = 0.4, label = player_B + ' Tackles in Defensive 3rd')
    plt.bar(X_axis + 0.2, table_B['Tackles - Mid 3rd'], bottom = table_B["Tackles - Def 3rd"], width = 0.4, label = player_B + ' Tackles in Middle Third')
    plt.bar(X_axis + 0.2, table_B['Tackles - Att 3rd'], bottom = (table_B["Tackles - Def 3rd"] + table_B["Tackles - Mid 3rd"]), width = 0.4, label = player_B + ' Tackles in Attacking 3rd')
    plt.ylabel("Tackles Made", size=12)
    plt.yticks(fontsize=12)
    plt.title("Tackles Made in 3 Different Areas per Season", size=18)

  # Vs Dribbles Section
  elif comparison == "Vs Dribbles - Dribblers Tackled":
    plt.bar(X_axis - 0.2, table_A['Vs Dribbles - Tkl'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Vs Dribbles - Tkl'], width = 0.4, label = player_B)
    plt.ylabel("Dribblers Tackled", size=12)
    plt.yticks(fontsize=12)
    plt.title("Dribblers Tackled per Season", size=18)
  
  elif comparison == "Vs Dribbles - Tackle Attempt Against Dribblers":
    plt.bar(X_axis - 0.2, table_A['Vs Dribbles - Att'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Vs Dribbles - Att'], width = 0.4, label = player_B)
    plt.ylabel("Tackle Attempts Against Dribblers", size=12)
    plt.yticks(fontsize=12)
    plt.title("Tackle Attempts Against Dribblers per Season", size=18)
  
  elif comparison == "Vs Dribbles - Tackles Against Dribblers %":
    plt.bar(X_axis - 0.2, table_A['Vs Dribbles - Tkl%'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Vs Dribbles - Tkl%'], width = 0.4, label = player_B)
    plt.ylabel("Tackle Against Dribblers Success Rate", size=12)
    plt.yticks(fontsize=12)
    plt.title("Tackle Against Dribblers Success Rate per Season", size=18)
  
  elif comparison == "Vs Dribbles - Dribbled Past":
    plt.bar(X_axis - 0.2, table_A['Vs Dribbles - Past'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Vs Dribbles - Past'], width = 0.4, label = player_B)
    plt.ylabel("Dribbled Past", size=12)
    plt.yticks(fontsize=12)
    plt.title("Dribbled Past per Season", size=18)
  
  elif comparison == "Tackle Attempts Against Dribblers Stack":
    plt.bar(X_axis - 0.2, table_A['Vs Dribbles - Past'], width = 0.4, label = player_A + ' Dribbled Past')
    plt.bar(X_axis - 0.2, table_A['Vs Dribbles - Tkl'], bottom = table_A["Vs Dribbles - Past"], width = 0.4, label = player_A + ' Tackles Won vs Dribblers')
    plt.bar(X_axis + 0.2, table_B['Vs Dribbles - Past'], width = 0.4, label = player_B + ' Dribbled Past')
    plt.bar(X_axis + 0.2, table_B['Vs Dribbles - Tkl'], bottom = table_B["Vs Dribbles - Past"], width = 0.4, label = player_B + ' Tackles Won vs Dribblers')
    plt.ylabel("Tackles vs Dribblers", size=12)
    plt.yticks(fontsize=12)
    plt.title("Tackle vs Dribblers per Season", size=18)
    
  # Pressures Section
  elif comparison == "Pressures - Press Attempts":
    plt.bar(X_axis - 0.2, table_A['Pressures - Press'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Pressures - Press'], width = 0.4, label = player_B)
    plt.ylabel("Press Attempts", size=12)
    plt.yticks(fontsize=12)
    plt.title("Press Attempts per Season", size=18)
  
  elif comparison == "Pressures - Press Successes":
    plt.bar(X_axis - 0.2, table_A['Pressures - Succ'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Pressures - Succ'], width = 0.4, label = player_B)
    plt.ylabel("Pressing Success", size=12)
    plt.yticks(fontsize=12)
    plt.title("Pressing Success per Season", size=18)
  
  elif comparison == "Pressures - Press Success %":
    plt.bar(X_axis - 0.2, table_A['Pressures - %'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Pressures - %'], width = 0.4, label = player_B)
    plt.ylabel("Pressing Success Rate", size=12)
    plt.yticks(fontsize=12)
    plt.title("Pressing Success Rate per Season", size=18)
  
  elif comparison == "Pressures Stack":
    table_A['Pressures - Press_Fails'] = table_A["Pressures - Press"] - table_A["Pressures - Succ"]
    table_B['Pressures - Press_Fails'] = table_B["Pressures - Press"] - table_B["Pressures - Succ"]
    plt.bar(X_axis - 0.2, table_A['Pressures - Press_Fails'], width = 0.4, label = player_A + ' Pressures Fail')
    plt.bar(X_axis - 0.2, table_A['Pressures - Succ'], bottom = table_A["Pressures - Press_Fails"], width = 0.4, label = player_A + ' Pressures Success')
    plt.bar(X_axis + 0.2, table_B['Pressures - Press_Fails'], width = 0.4, label = player_B + ' Pressures Fail')
    plt.bar(X_axis + 0.2, table_B['Pressures - Succ'], bottom = table_B["Pressures - Press_Fails"], width = 0.4, label = player_B + ' Pressures Success')
    plt.ylabel("Pressures", size=12)
    plt.yticks(fontsize=12)
    plt.title("Pressures per Season", size=18)
  
  elif comparison == "Pressures - Press in Def 3rd":
    plt.bar(X_axis - 0.2, table_A['Pressures - Def 3rd'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Pressures - Def 3rd'], width = 0.4, label = player_B)
    plt.ylabel("Pressures in Defensive 3rd", size=12)
    plt.yticks(fontsize=12)
    plt.title("Pressures in Defensive 3rd per Season", size=18)
  
  elif comparison == "Pressures - Press in Mid 3rd":
    plt.bar(X_axis - 0.2, table_A['Pressures - Mid 3rd'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Pressures - Mid 3rd'], width = 0.4, label = player_B)
    plt.ylabel("Pressures in Middle 3rd", size=12)
    plt.yticks(fontsize=12)
    plt.title("Pressures in Middle 3rd per Season", size=18)
  
  elif comparison == "Pressures - Press in Att 3rd":
    plt.bar(X_axis - 0.2, table_A['Pressures - Att 3rd'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Pressures - Att 3rd'], width = 0.4, label = player_B)
    plt.ylabel("Pressures in Attacking 3rd", size=12)
    plt.yticks(fontsize=12)
    plt.title("Pressures in Attacking 3rd per Season", size=18)
  
  elif comparison == "Pressures Area Stack":
    plt.bar(X_axis - 0.2, table_A['Pressures - Def 3rd'], width = 0.4, label = player_A + ' Pressures in Defensive 3rd')
    plt.bar(X_axis - 0.2, table_A['Pressures - Mid 3rd'], bottom = table_A["Pressures - Def 3rd"], width = 0.4, label = player_A + ' Pressures in Middle Third')
    plt.bar(X_axis - 0.2, table_A['Pressures - Att 3rd'], bottom = (table_A["Pressures - Def 3rd"] + table_A["Pressures - Mid 3rd"]), width = 0.4, label = player_A + ' Pressures in Attacking 3rd')
    plt.bar(X_axis + 0.2, table_B['Pressures - Def 3rd'], width = 0.4, label = player_B + ' Pressures in Defensive 3rd')
    plt.bar(X_axis + 0.2, table_B['Pressures - Mid 3rd'], bottom = table_B["Pressures - Def 3rd"], width = 0.4, label = player_B + ' Pressures in Middle Third')
    plt.bar(X_axis + 0.2, table_B['Pressures - Att 3rd'], bottom = (table_B["Pressures - Def 3rd"] + table_B["Pressures - Mid 3rd"]), width = 0.4, label = player_B + ' Pressures in Attacking 3rd')
    plt.ylabel("Pressures Made", size=12)
    plt.yticks(fontsize=12)
    plt.title("Pressures Made in 3 Different Areas per Season", size=18)
  
  # Blocks Section
  elif comparison == "Blocks - Blocks Made":
    plt.bar(X_axis - 0.2, table_A['Blocks - Blocks'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Blocks - Blocks'], width = 0.4, label = player_B)
    plt.ylabel("Blocks Made", size=12)
    plt.yticks(fontsize=12)
    plt.title("Blocks Made per Season", size=18)
  
  elif comparison == "Blocks - Shots Blocked":
    plt.bar(X_axis - 0.2, table_A['Blocks - Sh'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Blocks - Sh'], width = 0.4, label = player_B)
    plt.ylabel("Shots Blocked", size=12)
    plt.yticks(fontsize=12)
    plt.title("Shots Blocked per Season", size=18)
  
  elif comparison == "Blocks - Shots on Target Blocked":
    plt.bar(X_axis - 0.2, table_A['Blocks - ShSv'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Blocks - ShSv'], width = 0.4, label = player_B)
    plt.ylabel("Shots on Target Blocked", size=12)
    plt.yticks(fontsize=12)
    plt.title("Shots on Target Blocked per Season", size=18)
  
  elif comparison == "Blocks - Passes Blocked":
    plt.bar(X_axis - 0.2, table_A['Blocks - Pass'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Blocks - Pass'], width = 0.4, label = player_B)
    plt.ylabel("Passes Blocked", size=12)
    plt.yticks(fontsize=12)
    plt.title("Passes Blocked per Season", size=18)
  
  # Other Section
  elif comparison == "Interceptions":
    plt.bar(X_axis - 0.2, table_A['Int'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Int'], width = 0.4, label = player_B)
    plt.ylabel("Interceptions Made", size=12)
    plt.yticks(fontsize=12)
    plt.title("Interceptions Made per Season", size=18)
  
  elif comparison == "Tackles + Interceptions":
    plt.bar(X_axis - 0.2, table_A['Tkl+Int'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Tkl+Int'], width = 0.4, label = player_B)
    plt.ylabel("Tackles + Interceptions Made", size=12)
    plt.yticks(fontsize=12)
    plt.title("Tackles + Interceptions Made per Season", size=18)
  
  elif comparison == "Clearences":
    plt.bar(X_axis - 0.2, table_A['Clr'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Clr'], width = 0.4, label = player_B)
    plt.ylabel("Clearences", size=12)
    plt.yticks(fontsize=12)
    plt.title("Clearences per Season", size=18)
  
  elif comparison == "Errors Leading to Opponent's Shots":
    plt.bar(X_axis - 0.2, table_A['Err'], width = 0.4, label = player_A)
    plt.bar(X_axis + 0.2, table_B['Err'], width = 0.4, label = player_B)
    plt.ylabel("Errors Leading to Shots", size=12)
    plt.yticks(fontsize=12)
    plt.title("Errors Leading to Shots per Season", size=18)
  
  plt.legend(loc='best', framealpha=0.5)
  
  # adjusts the size of the chart to the size of the figure
  plt.tight_layout()
  
  # get the bytes data
  chart = get_graph()
  
  return chart


def get_graph():
  buffer = io.BytesIO()
  plt.savefig(buffer, format='png')
  buffer.seek(0)
  image_png = buffer.getvalue()
  graph = base64.b64encode(image_png)
  graph = graph.decode('utf-8')
  buffer.close()
  return graph