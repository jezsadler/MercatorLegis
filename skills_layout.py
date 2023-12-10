import pandas as pd
import html
import urllib.request
import re
from string import capwords

from bs4 import BeautifulSoup, Tag
from jinja2 import Environment, FileSystemLoader, select_autoescape


def generate_gang_quickref(cardpath):
    """Creates a quick reference sheet for the skills and 
    weapon traits used by a Necromunda gang, based on the
    YakTribe list for the gang."""
    # Load in the gang skills:
    universal = pd.read_csv("universalskills.csv")
    universal['Skill Set'] = universal['Skill Set'].apply(capwords)
    universal['Skill Name'] = universal['Skill Name'].apply(capwords)
    universal['Skill Name'] = universal['Skill Name'].str.replace('\u200b','')
 
    #Load in Wyrd Powers:
    wyrd = pd.read_csv("wyrdpowers.csv")
    wyrd["Combi Name"] = wyrd["Discipline"] + " - " + wyrd["Power Name"]

    actions =  pd.read_csv("actions.csv")

    # Load in the weapon traits:
    weapon_traits = pd.read_csv("weapontraits.csv")
    weapon_traits['Trait Name'] = weapon_traits['Trait Name'].apply(capwords)

    # TODO: add wargear and other special rules.
    armour = pd.read_csv("armour.csv")
    equipment = pd.read_csv("personalequipment.csv")
    genesmith = pd.read_csv("genesmith.csv")
    vehicles = pd.read_csv("vehicles.csv")

    wargear = pd.concat([armour,equipment,genesmith,vehicles],ignore_index=True)
    wargear['Wargear Name'] = wargear['Wargear Name'].apply(capwords)
    # wargear['Additional Rules'] = wargear['Additional Rules'].fillna('')

    special_rules = pd.read_csv("specials.csv")

    # These rules impact things outside of the battle, so don't need to
    # be on the quick reference.
    ignore_rules = ["gang fighter (ganger)","gang fighter (prospect)",
                    "gang fighter (juve)","gang fighter (crew)","gang leader",
                    "fast learner","tools of the trade","promotion (specialist)", 
                    "promotion (champion)","psychoteric whispers",
                    "infiltration","vatborn","unborn agility","unborn brawn", 
                    "unborn combat","unborn cunning","unborn ferocity","unborn shooting",
                    "unborn savant","fresh from the academy",]

    # Open the cards file from YakTribe:
    if cardpath.startswith("https://yaktribe.games/underhive/print/cards"):
        with urllib.request.urlopen(cardpath) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
    elif cardpath.startswith("LOCAL:"):
        cardfile = cardpath.split(":")[1]
        with open(cardfile) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
    else:
        gang_id = re.findall("(\d+)(?!.*\d)",cardpath)[0]
        cardpath = "https://yaktribe.games/underhive/print/cards/" + gang_id
        with urllib.request.urlopen(cardpath) as fp:
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
    
    # Group activation skills are a bit fiddly - 
    groupacts = {r for r in gang_rules if r.startswith("group activation") 
                 and r != "group activation (exotic beasts)"}
    gang_rules = {r for r in gang_rules if not r.startswith("group activation") 
                 or r == "group activation (exotic beasts)"}
    if len(groupacts) >= 1:
        gang_rules.add("group activation (x)")
    # Actions are only granted by other rules, not listed directly.
    gang_actions = set()

    # Get additional rules granted by written rules.
    check_traits = gang_weapon_traits
    check_skills = gang_skills
    check_wargear = gang_wargear
    check_rules = gang_rules
    while(
        len(check_traits) +
        len(check_skills) +
        len(check_wargear) +
        len(check_rules) > 0):
     
        additional = {}
        add_from_traits = weapon_traits[
            weapon_traits['Trait Name'].str.lower().isin(check_traits)
            & weapon_traits['Additional Rules'].notna()]
        add_from_skills = universal[
            universal["Skill Name"].str.lower().isin(check_skills)
            & universal['Additional Rules'].notna()]['Additional Rules']
        add_from_wyrd = wyrd[
            (wyrd["Power Name"].str.lower().isin(check_skills) |
            wyrd["Combi Name"].str.lower().isin(check_skills))
            & wyrd['Additional Rules'].notna()]['Additional Rules']
        add_from_wargear = wargear[
            wargear["Wargear Name"].str.lower().isin(check_wargear)
            & wargear['Additional Rules'].notna()]['Additional Rules']
        add_from_specials = special_rules[
            special_rules["Rule"].str.lower().isin(check_rules)
            & special_rules['Additional Rules'].notna()]['Additional Rules']
        for add_rules in [add_from_traits,
                        add_from_skills,
                        add_from_wyrd,
                        add_from_wargear,
                        add_from_specials,]:
            if len(add_rules) > 0:
                for ar in add_rules:
                    for k,v in eval(ar).items():
                        if k in additional:
                            for i in v:
                                additional[k].add(i.lower())
                        else:
                            additional[k] = {i.lower() for i in v}
        if 'Actions' in additional.keys():
            gang_actions = gang_actions.union(additional['Actions'])
        if 'Weapon Traits' in additional.keys():
            check_traits = {
                trait for trait in additional['Weapon Traits']
                if trait not in gang_weapon_traits}
            gang_weapon_traits = gang_weapon_traits.union(gang_weapon_traits)
        else:
            check_traits = {}
        if 'Special Rules' in additional.keys():
            check_rules = {
                rule for rule in additional['Special Rules']
                if rule not in gang_rules}
            gang_rules = gang_rules.union(check_rules)
        else:
            check_rules = {}
        if 'Skills' in additional.keys():
            check_skills = {
                skill for skill in additional['Skills']
                if skill not in gang_skills}
            gang_skills = gang_skills.union(check_skills)
        else:
            check_skills = {}
        if 'Wyrd Powers' in additional.keys():
            check_powers = {
                power for power in additional['Wyrd Powers']
                if power not in gang_skills}
            check_skills = check_skills.union(check_powers)
            gang_skills = gang_skills.union(check_powers)
        if 'Wargear' in additional.keys():
            check_wargear = {gear for gear in additional['Wargear']
                           if gear not in gang_wargear}
            gang_wargear = gang_wargear.union(check_wargear)
        else:
            check_wargear = {}


    # Filter the big tables to what this gang needs.
    gang_trait_table = weapon_traits[weapon_traits['Trait Name'].str.lower().isin(gang_weapon_traits)]
    gang_skill_table = universal[universal["Skill Name"].str.lower().isin(gang_skills)]

    gang_wyrd_table = wyrd[wyrd["Power Name"].str.lower().isin(gang_skills) |
                           wyrd["Combi Name"].str.lower().isin(gang_skills)]

    gang_wargear_table = wargear[wargear["Wargear Name"].str.lower().isin(gang_wargear)]
    gang_specials_table = special_rules[special_rules["Rule"].str.lower().isin(gang_rules)]

    for table in [gang_trait_table,gang_skill_table,gang_wyrd_table,gang_wargear_table,gang_specials_table]:
        filled = table["Additional Rules"].fillna("{'Actions':None}")
        action_list = []
        for row in filled.apply(eval):
            if 'Actions' in row.keys():
                action_list.append(row['Actions'])
            else:
                action_list.append(None)
        table.insert(len(table.columns),"Actions",pd.Series(action_list,index=table.index,name="Actions"))

    add_rules_as_dicts = []
    for add_rule in gang_wargear_table["Additional Rules"]:
        if isinstance(add_rule,str):
            add_rules_as_dicts.append(eval(add_rule))
        else:
            add_rules_as_dicts.append(None)
    gang_wargear_table.loc[:,"Additional Rules"] = pd.Series(add_rules_as_dicts,index=gang_wargear_table.index)

    gang_actions_table = actions[actions["Action Name"].str.lower().isin(gang_actions)]
    # Hide Wyrd Powers, Wargear, Special rules tables if they're empty.
    if len(gang_wyrd_table) == 0:
        gang_wyrd_table = None
    if len(gang_wargear_table) == 0:
        gang_wargear_table = None
    if len(gang_specials_table) == 0:
        gang_specials_table = None

    unknown_traits = [t for t in gang_weapon_traits if t not in list(weapon_traits['Trait Name'].str.lower())]
    unknown_skills = [s for s in gang_skills if s not in list(universal["Skill Name"].str.lower())
                      and s not in list(wyrd["Power Name"].str.lower())
                      and s not in list(wyrd["Combi Name"].str.lower())]
    unknown_wargear = [w for w in gang_wargear if w not in ignore_rules
                       and w not in list(wargear["Wargear Name"].str.lower())]
    unknown_special = [r for r in gang_rules if r not in ignore_rules 
                       and r not in list(special_rules["Rule"].str.lower())]
    ignore_wargear = [w for w in gang_wargear if w in ignore_rules]
    ignore_special = [r for r in gang_rules if r in ignore_rules]

    unknown_rules = set(unknown_traits + unknown_skills + unknown_wargear + unknown_special)
    unknown_rules.discard('')
    if unknown_rules == set():
        unknown_rules = None

    ignore_gang = set(ignore_wargear + ignore_special)
    if ignore_gang == set():
        ignore_gang = None

    return gang_name,gang_type,gang_skill_table,gang_wyrd_table,gang_specials_table,gang_trait_table,gang_wargear_table,gang_actions_table,unknown_rules,ignore_gang
