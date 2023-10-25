import pandas as pd
import html
import urllib.request 

from bs4 import BeautifulSoup, Tag
from jinja2 import Environment, FileSystemLoader, select_autoescape


def generate_gang_quickref(cardpath):
    """Creates a quick reference sheet for the skills and 
    weapon traits used by a Necromunda gang, based on the
    YakTribe list for the gang."""
    # Load in the gang skills:
    universal = pd.read_csv("universalskills.csv")
    universal['Skill Set'] = universal['Skill Set'].str.title()
    universal['Skill Name'] = universal['Skill Name'].str.replace('\u200b','')
    actions =  universal['Action'].fillna(0)
    universal['Action'] = actions

    # Load in the weapon traits:
    weapon_traits = pd.read_csv("weapontraits.csv")
    weapon_traits['Trait Name'] = weapon_traits['Trait Name'].str.title()

    # TODO: add wargear and other special rules.

    # Open the cards file from YakTribe:
    if cardpath.startswith("https://yaktribe.games/underhive/gang/"):
        gang_id = cardpath.split(".")[-1].replace("/","")
        cardpath = "https://yaktribe.games/underhive/print/cards/" + gang_id
        with urllib.request.urlopen(cardpath) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
    elif cardpath.startswith("https://yaktribe.games/underhive/print/cards"):
        with urllib.request.urlopen(cardpath) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
    else:
        with open(cardpath) as fp:
            soup = BeautifulSoup(fp, 'html.parser')

    # Get the gang name:
    gang_name = soup.title.contents[0]
    gang_type = soup.body.find_all("table")[-2].find_all('td')[0].contents[0]

    # Get the ganger names. Currently not using these for anything.
    ganger_names = [name.contents[1].text.rstrip() for name in soup.find_all("h5")][:-1]

    # Parse the weapon tables on the cards to get the weapon traits. 
    gang_weapon_traits = []

    weapon_tables = soup.find_all("table","gang-ganger-weapons")
    # Each element of weapon_tables represents the weapons on one
    # fighter card. The top 
    for w in weapon_tables:
        for row in w.find_all("tr")[1:]:
            traits = row.contents[-2].contents[0].text.lstrip().rstrip().split(',')
            gang_weapon_traits += traits

    # Group the skills with parameters (e..g. Rapid Fire (X))
    x_traits = [t.split('(')[0].lower()+'(x)' for t in gang_weapon_traits if '(' in t]

    gang_weapon_traits = set([t.lower() for t in gang_weapon_traits if '(' not in t] + x_traits)

    # Now parse the card sections after the weapon table, for 
    # wargear, skills, and special rules.
    non_weapons = soup.find_all("table","table table-sm mb-1")

    gang_wargear = []
    gang_skills = []
    gang_rules = []

    for nw in non_weapons:
        for row in nw.contents[1].contents:
            if isinstance(row,Tag):
                label = row.contents[1].contents[0]
                values = row.contents[3].contents[0].lstrip().rstrip().split(',')
                values = [v.replace(',','').lstrip().rstrip() for v in values]
                if label == 'SKILLS':
                    gang_skills += values
                elif label == 'WARGEAR':
                    gang_wargear += values
                elif label == 'RULES':
                    gang_rules += values

    gang_wargear = {gear.lower() for gear in gang_wargear if gear != ''}
    gang_skills = {skill.lower() for skill in gang_skills if skill != ''}
    gang_rules = {rule.lower() for rule in gang_rules if rule != ''}

    # Filter the big tables to what this gang needs.
    gang_trait_table = weapon_traits[weapon_traits['Trait Name'].str.lower().isin(gang_weapon_traits)]
    gang_skill_table = universal[universal["Skill Name"].str.lower().isin(gang_skills)]

    return gang_name,gang_type,gang_skill_table,gang_trait_table