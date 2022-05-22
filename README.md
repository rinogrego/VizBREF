# VizBREF

<!-- <p align="middle">
  <img src="/images/fb-logo.svg" height="150" width="350"/>
  <img src="/images/sr-logo.svg" height="150" width="350"/>
</p> -->
<div align="center">
  <h2>Preview</h2>
  <img src="/dashboard/static/images/Vizbref.PNG" height="500" width="700" /> <br><br>
  <img src="/dashboard/static/images/vizbref-compare.gif" height="500" width="700" />
</div>
<div align="center">
  <h2>Data Source</h2>
  <img src="/dashboard/static/images/fb-logo.svg" height="150" width="350" /> &nbsp; &nbsp; &nbsp;
  <img src="/dashboard/static/images/sr-logo.svg" height="150" width="350" />
</div>

[Fbref](https://fbref.com/en/) statistics visualization automation website.

## About
A website to automatically generate visualizations of comparisons between 2 football players with data scraped from fbref website. Scraping, data cleaning, data aggregation, and visualizations are done automatically at the backend. Players covered are players listed from fbref data from 5 leagues: Premier League, La Liga, Bundesliga, Serie A, and Ligue 1, in season 2021/2022 (May of 2022). 

The seasons for comparison are based upon the last few seasons 2 players shared together (e.g. if player A data have been tracked since 2014/2015 and player B data have been tracked from 2017/2018 then the earliest season the comparison can be plotted is from season 2017/2018 onwards). If there is a season in the plot where 1 player have a plot for that season while the other don't (or both don't) then the either the value is really 0 or metric/data probably haven't been computed yet at that time for that player(s), which is the most cases.

## Categories
There are four categories available for comparisons, each with their own metrics:
- Standard Statistic
    - Minutes Played
    - Starts
    - Matches Played
    - 90s
    - Starts Stack (stacked bar chart for Starter and non-Starter Matches Played)
    - Expected Goals (xG)
    - Expected non-Penalty Goals (npxG)
    - Expected Assists (xA)
    - Expected non-Penalty Goals + Expected Assists (npxG+xA)
- Shooting
    - Goals
    - Shots
    - Shots on Target
    - Shots on Target rate
    - Shots per 90
    - Shots on Target per 90
    - Goals per Shots
    - Goals per Shots on Target
    - Average Distance of Shots Taken from Goal
    - Goals Stack (stacked bar chart for Goals + non-Penalty Goals)
    - Expected Goals
    - Expected non-Penalty Goals
    - Goals - Expected Goals
    - Goals - Expected Goals (non-Penalty)
- Passing
    - Total/Short/Medium/Long Passes Completed
    - Total/Short/Medium/Long Passes Attempted
    - Total/Short/Medium/Long Pass Completion rate
    - Total Passes Distance
    - Total Progressive Passes Distance
    - Assists
    - Expected Assists
    - Assists - Expected Assists
    - Final Third Passes
    - Passes into Penalty Area
    - Cross into Penalty Area
    - Progressive Passes
- Defensive Actions
    - Tackles Made
    - Tackles Won
    - Tackles in Defensive/Middle/Attacking Third
    - Tackles Area Stack (stacked bar chart for tackles made in each 3rd)
    - Dribblers Tackled
    - Tackle Attempt Against Dribblers
    - Tackles Against Dribblers Success rate
    - Dribbled Past
    - Tackle Attempts Against Dribblers Stack
    - Pressure Attempts
    - Press Success
    - Press Success rate
    - Pressure Stack (stacked bar chart for succeed and failed pressures)
    - Pressures in Defensive/Middle/Attacking 3rd
    - Pressure Area Stack (stacked bar chart for pressures made in each 3rd)
    - Blocks Made
    - Shots Blocked
    - Shots on Target Blocked
    - Passes Blocked
    - Interceptions Made
    - Tackles + Interceptions Made
    - Clearences
    - Errors Leading to Opponent's Shots

## How it works
1. User will choose 2 players to compare
2. The backend will find fbref's id for each player from internal reference
3. Once retrieved, the backend will scrap their data from fbref's player page
4. The scraped data will be cleaned, aggregated, and then plotted automatically
5. Each plot will be sent as encoded data (with io and base64 modules)
6. The plots will be displayed as images in the HTML page

## Tools and libraries used
- Django 
- Pandas
- Numpy
- Matplotlib
- Beautifulsoup4
- Request
- Git
- Gunicorn
- Heroku

<!-- ## Deployment Locally (Windows)
1. Create a folder for the project and then go to that folder
2. Activate virtual environment
```
python -m venv ENV_NAME
.\ENV_NAME\Scripts\Activate
```
3. Go to a terminal for the project folder and clone the repository
```
git clone https://github.com/rinogrego/VizBREF
```
4. Go to the folder of cloned repository
```
cd VizBref
```
5. Install all the necessary packages
```
pip install -r requirements.txt
```
6. Run
```
python manage.py runserver
```
7. Accessing the website, go to: 127.0.0.1:8000 -->
