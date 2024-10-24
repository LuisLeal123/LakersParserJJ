# Objective:
# Parse through every espn laker game with an input of nba players
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import re

driver = webdriver.Chrome()

# Store the data on a hashmap
mapping = {}
wins = 0
losses = 0
pointsScored = 0
pointsAgainst = 0


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.google.com',
    'DNT': '1'
}

# Extract numeric values from the score divs
def extract_score(score_div):
    return int(re.search(r'\d+', score_div.text.strip()).group()) if score_div else None


def addstuff(x):
    global wins, losses, pointsScored, pointsAgainst

    # Select the scores
    left_score_div = x.select_one(
        '#fittPageContainer > div.pageContent > div > div > div:nth-child(1) > div > div > '
        'div.Gamestrip__Team--left > div > div.Gamestrip__ScoreContainer > div.Gamestrip__Score'
    )
    right_score_div = x.select_one(
        '#fittPageContainer > div.pageContent > div > div > div:nth-child(1) > div > div > '
        'div.Gamestrip__Team--right > div > div.Gamestrip__ScoreContainer > div.Gamestrip__Score'
    )

    # Extract numeric values from the divs
    left_score = extract_score(left_score_div)
    right_score = extract_score(right_score_div)

    # Check team logos (alt text) to identify which team is the Lakers
    left_team_logo = x.select_one(
        '#fittPageContainer > div.pageContent > div > div > div:nth-child(1) > div > div > '
        'div.Gamestrip__Team--left img'
    )
    right_team_logo = x.select_one(
        '#fittPageContainer > div.pageContent > div > div > div:nth-child(1) > div > div > '
        'div.Gamestrip__Team--right img'
    )

    left_team = left_team_logo['alt'] if left_team_logo else None
    right_team = right_team_logo['alt'] if right_team_logo else None

    # Determine which team is the Lakers
    if "Lakers" in left_team:
        lakers = left_score
        nonlakers = right_score
    else:
        lakers = right_score
        nonlakers = left_score

    pointsScored += lakers
    pointsAgainst += nonlakers
    wins += 1 if lakers > nonlakers else 0
    losses += 1 if lakers < nonlakers else 0



# Initialize the mapping with 14 stats and set the first element for the count
def process_player(player_name, new_stats):
    if player_name not in mapping:
        # Initialize player's entry with the count (1) and 14 stats initialized to 0
        mapping[player_name] = [1] + [0] * 14
    else:
        # Increment the times found
        mapping[player_name][0] += 1

    # Add new stats to the existing stats (starting from index 1)
    for idx in range(len(new_stats)):
        mapping[player_name][idx + 1] += new_stats[idx]


# Main function, x is a list
def main(x):
    # Iterate through ESPN's
    url = "https://www.espn.com/nba/team/schedule/_/name/lal/season/2024"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    game_links = soup.find_all('a', class_='AnchorLink')

    filtered_game_links = [link.get('href') for link in game_links if 'gameId' in link.get('href')]

    # Iterate through filtered game links
    for href in filtered_game_links:
        print(f"Processing game link: {href}")
        full_url = f"{href}"
        linked_page_response = requests.get(full_url, headers=headers)

        linked_page_soup = BeautifulSoup(linked_page_response.content, 'html.parser')
        box_score_link = linked_page_soup.select_one('a[href*="/boxscore/"]')

        if box_score_link:
            box_score_href = box_score_link.get('href')
            box_score_url = f"https://www.espn.com{box_score_href}"

            box_score_response = requests.get(box_score_url, headers=headers)
            box_score_soup = BeautifulSoup(box_score_response.content, 'html.parser')

            # Check if "Los Angeles Lakers" is found in div:nth-child(1) or div:nth-child(2)
            team1 = box_score_soup.select_one(
                '#fittPageContainer > div.pageContent > div > div > div:nth-child(6) > div > div > section.Card.Card__TableTopBorder > div > div > div > div:nth-child(1) > div > div.Boxscore__Title.flex.items-center.pt3.pb3.brdr-clr-gray-08 > div')
            team2 = box_score_soup.select_one(
                '#fittPageContainer > div.pageContent > div > div > div:nth-child(6) > div > div > section.Card.Card__TableTopBorder > div > div > div > div:nth-child(2) > div > div.Boxscore__Title.flex.items-center.pt3.pb3.brdr-clr-gray-08 > div')

            if team1 and "Los Angeles Lakers" in team1.text:
                lakers_team_div = box_score_soup.select_one(
                    '#fittPageContainer > div.pageContent > div > div > div:nth-child(6) > div > div > section.Card.Card__TableTopBorder > div > div > div > div:nth-child(1) > div.Boxscore.flex.flex-column > div.ResponsiveTable.ResponsiveTable--fixed-left.Boxscore.flex.flex-column > div > table > tbody')
            elif team2 and "Los Angeles Lakers" in team2.text:
                lakers_team_div = box_score_soup.select_one(
                    '#fittPageContainer > div.pageContent > div > div > div:nth-child(6) > div > div > section.Card.Card__TableTopBorder > div > div > div > div:nth-child(2) > div.Boxscore.flex.flex-column > div.ResponsiveTable.ResponsiveTable--fixed-left.Boxscore.flex.flex-column > div > table > tbody')

            # If valid box found, process the players
            if lakers_team_div:
                found_players = set()
                for i in range(2, 16):  # Assuming player rows start at 2nd child
                    player = lakers_team_div.select_one(f'tr:nth-child({i}) > td > div > a.AnchorLink')
                    if player:
                        player_name = player['href'].split('/')[-1]  # Extract the player slug

                        # Check if the player has numbers or "DNP-COACH'S DECISION"
                        stats_row = box_score_soup.select(f'tr:nth-child({i}) > td')
                        valid_player = False

                        for stat in stats_row:
                            stat_text = stat.text.strip()
                            if stat_text.isdigit():
                                valid_player = True  # Player has stats
                                break
                            elif "DNP-COACH'S DECISION" in stat_text:
                                valid_player = True  # Player has "DNP-COACH'S DECISION"
                                break

                        if valid_player and player_name in x:
                            found_players.add(player_name)  # Add player if valid

                # Check if any player from 'x' is missing
                missing_players = x - found_players
                if missing_players:
                    print(f"Missing players: {missing_players}")

                # process their stats
                else:
                    print("All players found.")
                    addstuff(box_score_soup)
                    # Iterate through each player and gather their stats
                    for i in range(2, 16):  # Adjust range for the number of players
                        player = lakers_team_div.select_one(f'tr:nth-child({i}) > td > div > a')
                        if player:
                            player_name = player.text.strip()

                            # Gather the player's stats from columns 1 to 14
                            stats = []
                            for j in range(1, 15):  # Loop through stats columns (1 to 14)
                                # Adjust the selector to include the stats from the correct div
                                stat = box_score_soup.select_one(
                                    f'#fittPageContainer > div.pageContent > div > div > div:nth-child(6) > div > div > '
                                    f'section.Card.Card__TableTopBorder > div > div > div > div:nth-child(2) > '
                                    f'div.Boxscore.flex.flex-column > div.ResponsiveTable.ResponsiveTable--fixed-left.Boxscore.flex.flex-column > '
                                    f'div > div > div.Table__Scroller > table > tbody > tr:nth-child({i}) > td:nth-child({j})'
                                )
                                if stat:
                                    try:
                                        stat_value = int(stat.text.strip())  # Convert stat to integer
                                        stats.append(stat_value)
                                    except ValueError:
                                        pass  # Skip if the stat is not a number

                            # Process player stats and update mapping
                            process_player(player_name, stats)

        else:
            break  # Break the loop if no more links are found

    return mapping

set1 = {"lebron-james", "anthony-davis", "rui-hachimura", "max-christie", "jaxson-hayes", "austin-reaves", "dangelo-russell"}
set2 = {"lebron-james"}
main(set2)

print(wins)
print(losses)
print(pointsScored/(wins+losses))
print(pointsAgainst/(wins+losses))
print(mapping)