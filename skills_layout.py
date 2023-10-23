import pandas as pd
import html

from bs4 import BeautifulSoup, Tag
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Load in the gang skills:
# TODO: include gang-specific skill sets
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
with open("cards.html") as fp:
    soup = BeautifulSoup(fp, 'html.parser')

# Get the gang name:
gang_name = soup.title.contents[0]
gang_type = soup.body.find_all("table")[-2].find_all('td')[0].contents[0]

# Get the ganger names. Currently not using these for anything.
ganger_names = [name.contents[1].text.rstrip() for name in soup.find_all("h5")][:-1]

# Parse the weapon tables on the cards to get the weapon traits. 
gang_weapon_traits = []

weapon_tables = soup.find_all("table","gang-ganger-weapons")
for w in weapon_tables:
    traits = w.contents[-2].contents[-2].contents[0].text.lstrip().rstrip().split(',')
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

# Set up Jinja2 environment. 
env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())

# Load this gang's data into template. 
template = env.get_template("srqr_template.html")

filename = f"{gang_name.replace(' ','')}QuickRef.html"

with open(filename, mode="w", encoding="utf-8") as quickref:
    quickref.write(template.render({"gang_name":gang_name,
                                    "gang_type":gang_type,
                                    "gang_skills":gang_skill_table,
                                    "weapon_traits":gang_trait_table}))
    print(f"... wrote {filename}")