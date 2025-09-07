#I condidered:
#chance of getting of getting one champion = chance of getting one Legacy Piece (meaning the chance 50% into each group)
#       i did this based on my Epic pulls since they are close to 50 % of each and if it wasnt
#       grouped the amount of epic champions would be bigger in comparison to epic pieces
#       this isnt as noticeble in Legendary since their numbers are close, i dont have a sample of REAL data big enough
#       to verify this however the values that i have are closer to 50-50 that the expected ( and these are "tempered" by
#       the previous boosted Legendary champions
#       On the mythics I also dont have an sample big enough but the number of Legacy pieces is also superior to the expected
#I Pity legendary the Legendary part uses the section that would be for epic eg. 3.84% chance of mythic 
#       Can be this, can be other values, they can grow in equal parts anyways the chance of legendary pity is ≈13.42%.
#The amount of Limited Mythics that i got in this script are superior to the observed by me with and personal average of ~80
#       to the expected by the program of ~62. This may be just bad luck for me 
#to add future heros they just need to be added to:
#   banner_Mythic_champions
#   Mythic_legacy
#   legendary_champions
#   legendary_legacy
#   epic_champions
#   epic_legacy

"""

The chances of obtaining Mythic and Legendary Champions or Legacy Pieces are as follows:
The base chance of obtaining a Mythic Champion or Legacy Piece is 3% (3.84% combined with guarantees).You are guaranteed a Mythic Champion or Legacy Piece within 50 draws.
The base chance of obtaining a Legendary Champion or Legacy Piece is 16% (17.79% combined with guarantees). You are guaranteed a Legendary or higher rarity Champion or Legacy Piece within 10 draws.
Upon obtaining a Mythic Champion or Legacy Piece, there is a 5% base chance (26.9% combined with guarantees) that it will be the limited Mythic Champion of the current event session. If you fail three times, the next Mythic Champion you obtain is guaranteed to be the limited one.
Upon obtaining a Mythic Champion or Legacy Piece, there is a 50% base chance (36.5% combined with guarantees) that it will be an odds-boosted, non-limited Mythic Champion of the current event session.
For the first 6 non-limited Mythic Champions or Legacy Pieces obtained from each Hypertime Tracker, you'll receive 2, 3, or 5 shards of the limited Mythic Champion of the current event session as a bonus with 60%, 35%, and 5% chances, respectively. Starting with the 7th non-limited Mythic Champion or Legacy Piece obtained, there is a 33% chance to receive 2, 3, or 5 shards of the limited Mythic Champion.

"""
import math
import random
import numpy as np
import matplotlib.pyplot as plt
import re
from collections import Counter
from collections import defaultdict
import mplcursors
import pandas as pd
from scipy.stats import skew, kurtosis

# Constants 
MYTHIC_RATE = 0.03 #0.0384
LEGENDARY_RATE = 0.16 #0.1779
EPIC_RATE = 1 - (MYTHIC_RATE + LEGENDARY_RATE)
MYTHIC_GUARANTEE = 50
LEGENDARY_GUARANTEE = 10
MYTHIC_BANNER_CHANCE = 0.05 #0.269
#LEGENDARY_BOOSTED_CHANCE = 0.5 #OBSULENT
MYTHIC_BOOSTED_CHANCE = 0.5

MAX_MYTHIC_PITY = MYTHIC_GUARANTEE - 1
MAX_BANNER_PITY = 3
MAX_LEGENDARY_PITY = LEGENDARY_GUARANTEE - 1

LEGACY_PIECE_CHANCE =  MYTHIC_BANNER_CHANCE + MYTHIC_BOOSTED_CHANCE + (1 - MYTHIC_BANNER_CHANCE - MYTHIC_BOOSTED_CHANCE) / 2
SHARDS_2_ODDS = 0.60
SHARDS_3_ODDS = 0.35
SHARDS_5_ODDS = 0.05
SHARDS_EXTRA_ODDS = (1/3)
###################
SHARD_THRESHOLDS = [
    (40, "Unlocked"),
    (42, "1 White Star"),
    (45, "2 White Stars"),
    (50, "3 White Stars"),
    (60, "4 White Stars"),
    (80, "5 White Stars"),
    (100, "1 Blue Star"),
    (120, "2 Blue Stars"),
    (140, "3 Blue Stars"),
    (170, "4 Blue Stars"),
    (200, "5 Blue Stars"),
    (240, "1 Purple Star"),
    (280, "2 Purple Stars"),
    (320, "3 Purple Stars"),
    (360, "4 Purple Stars"),
    (400, "5 Purple Stars"),
    (440, "1 Gold Star"),
    (480, "2 Gold Stars"),
    (520, "3 Gold Stars"),
    (580, "4 Gold Stars"),
    (640, "5 Gold Stars"),
    (720, "1 Red Star"),
    (800, "2 Red Stars"),
    (880, "3 Red Stars"),
    (960, "4 Red Stars"),
    (1040, "5 Red Stars"),
]
# Pools
# Banner Mythic champions (one will be randomly selected as banner)
banner_Mythic_champions = []
Mythic_legacy = []
legendary_champions = []
legendary_legacy = []
epic_champions = []
epic_legacy = []
banner_Mythic_champ =""
boosted_Mythic_champs = []

# State
mythic_pity = 0
legendary_pity = 0
non_banner_Mythics_since_last = 0
forced_Mythic_count = 0
forced_banner_Mythic_count = 0
numbers_of_non_banner_mysthic_pulls = 0
# Logging
results = Counter()
history = []
###
session_params = (0, 0, 0, 0)

def set_pull_list_to_default():

    global ordered_banners,Mythic_champions,banner_Mythic_champions,Mythic_legacy,legendary_champions,legendary_legacy,epic_champions,epic_legacy,boosted_Mythic_champs,banner_Mythic_champ
    # Pools
    Mythic_champions = [
        "Harley Quinn", "Batman", "Cyborg", "Two-Face", "Robin", "Doctor Fate",
        "Aquaman", "Shazam", "The Flash", "The Penguin", "Deadshot", "Batgirl",
        "Red Robin", "Lex Luthor", "Poison Ivy", "Bane", "Raven",
        "Black Canary", "Stargirl", "Arsenal","Krypto"
    ]
    banner_Mythic_champions = [
        "Superman", "Joker", "Sinestro", "Constantine", "Zatanna","Deathstroke",
        "Nightwing", "Hawkgirl", "Scarecrow","Martian Manhunter","Starfire","Supergirl","Superboy","Ra's al Ghul",
        "Talia","Hippolyta"
    ]
    Mythic_legacy = [
        "Purple Ray Radiation", "Modified Joker Venom Grenade", "Mind Control Hat",
        "Dark with Poison Ivy poison", "Amazonium Alloy Shield", "T-Sphere Weakness Analyzer",
        "Gabriel Horn", "Duplication Mirror", "Tectonic Disruptor", "Promethium Claws",
        "Robot Duplicate", "Imp Doll", "Starheart Staff"
    ]
    legendary_champions = [
        "Black Adam", "Killer Croc", "Vixen", "Catwoman", "Captain Cold",
        "The Atom", "Mera", "Red Hood", "Green Arrow", "Wonder Woman"
    ]
    legendary_legacy = [
        "Gas Derringer", "Explosive Javelin", "Energy Mace", "Cocoon Gun",
        "Plastic Explosive", "Coluan Force Field belt", "Improved Fear Gas Vial",
        "Cold Gun", "Not-So-Huge hammer"
    ]
    epic_champions = [
        "Shield Squad", "Patrolman", "Cross Bar", "Bang Bang", "Gatling Gal",
        "Bazooka Bro", "Chop Chop", "Home Fun", "Big Boy", "Good Day AK"
    ]
    epic_legacy = [
        "Pied Piper Flute", "Razor Rib Umbrella", "Flash-Bulb Kite",
        "Modoran Sonic Bomb", "Replica Time Commander", "Lawton Rifle Scope"
    ]
def set_banner(selected_banner=""):
    set_pull_list_to_default()
    global banner_Mythic_champ, boosted_Mythic_champs, Mythic_champions
    banner_boosted_map = {
        "Superman": ["Cyborg", "The Flash", "Shazam"],
        "Joker": ["Bane", "Harley Quinn", "Two-Face"],
        "Scarecrow": ["Aquaman", "The Penguin", "Poison Ivy"],
        "Deathstroke": ["Cyborg", "Deadshot", "Batgirl"],
        "Sinestro": ["Black Canary", "Lex Luthor", "Stargirl"],
        "Zatanna": ["Doctor Fate", "Raven", "Robin"],
        "Constantine": ["Doctor Fate", "The Flash", "Shazam"],
        "Nightwing": ["Batgirl", "Red Robin", "Robin"],
        "Supergirl": ["Aquaman", "The Flash", "Shazam"],
        "Superboy": ["The Flash", "Raven", "Two-Face"],
        "Hawkgirl": ["Aquaman", "Black Canary", "Harley Quinn"],
        "Martian Manhunter": ["Arsenal", "Stargirl", "Bane"],
        "Stargirl": ["Arsenal", "The Penguin", "Poison Ivy"],
        "Ra's al Ghul": ["Cyborg", "Krypto", "Robin"],
        "Talia": ["Bane", "Batgirl", "Harley Quinn"],
        "Hippolyta":["Harley Quinn","Two-Face","Deadshot"]
    }

    #ordered_banners = ["Superman", "Joker", "Scarecrow", "Deathstroke","Sinestro", "Zatanna", "Constantine", "Nightwing","Supergirl", "Superboy", "Hawkgirl", "Martian Manhunter","Stargirl", "Ra's al Ghul", "Talia"]
    banner_Mythic_champ = selected_banner
    boosted_Mythic_champs = set(banner_boosted_map.get(selected_banner, []))
def clean(m_pity=0, l_pity=0, non_banner_m_since_last=0,forced_m_count=0,forced_banner_m_count=0,res=Counter(),his=[],n_of_non_banner_m_pulls=0):
    global mythic_pity, legendary_pity, non_banner_Mythics_since_last,forced_Mythic_count,forced_banner_Mythic_count,results,history,numbers_of_non_banner_mysthic_pulls
    mythic_pity = m_pity
    legendary_pity = l_pity
    non_banner_Mythics_since_last = non_banner_m_since_last
    forced_Mythic_count = forced_m_count
    forced_banner_Mythic_count = forced_banner_m_count
    numbers_of_non_banner_mysthic_pulls = n_of_non_banner_m_pulls
    # Logging
    results = res
    history = his
def get_extra_shards(numbers_of_non_banner_mysthic_pulls):
    #return 0
    extra_shards = 0
    if numbers_of_non_banner_mysthic_pulls < 7 or random.random() < SHARDS_EXTRA_ODDS :
        number = random.random()
        if number < SHARDS_2_ODDS:
            extra_shards = 2
        elif number < SHARDS_2_ODDS+SHARDS_3_ODDS:
            extra_shards = 3
        else:
            extra_shards = 5 
    return extra_shards 
def draw(first_draw=False): # adapted for GUI
    global mythic_pity, legendary_pity, non_banner_Mythics_since_last,forced_Mythic_count,forced_banner_Mythic_count,numbers_of_non_banner_mysthic_pulls
    
    if first_draw:
        clean()
        mythic_pity = session_params[0]
        legendary_pity = session_params[1]
        non_banner_Mythics_since_last = session_params[2]
        numbers_of_non_banner_mysthic_pulls = session_params[3]
    mythic_pity += 1
    legendary_pity += 1
    extra_shards = 0

    roll = random.random()

    # Handle Mythic pity
    if mythic_pity >= MYTHIC_GUARANTEE:
        rarity = 'Mythic'
        forced_Mythic_count += 1
    elif legendary_pity >= LEGENDARY_GUARANTEE:
            if roll < MYTHIC_RATE:
                rarity = 'Mythic'
            else:
                rarity = 'Legendary'
    elif roll < MYTHIC_RATE:
        rarity = 'Mythic'
    elif roll < MYTHIC_RATE + LEGENDARY_RATE:
        rarity = 'Legendary'
    else:
        rarity = 'Epic'

    if rarity == 'Mythic':
        mythic_pity = 0
        legendary_pity = 0
        if(non_banner_Mythics_since_last >= 3):
            selected = banner_Mythic_champ #Forced Banner
            non_banner_Mythics_since_last = 0
            forced_banner_Mythic_count += 1
        else:
            rand = random.random()
            if rand < MYTHIC_BANNER_CHANCE:
                selected = banner_Mythic_champ #Natural Banner
                non_banner_Mythics_since_last = 0
            else:
                if rand < MYTHIC_BANNER_CHANCE+MYTHIC_BOOSTED_CHANCE:
                    selected = random.choice(list(boosted_Mythic_champs)) #Boosted Mythic   
                elif rand < LEGACY_PIECE_CHANCE: # 50% of the remaining
                    selected = random.choice(Mythic_legacy) #Legacy Piece
                else:
                    #Champion
                    pool = [
                        champ for champ in Mythic_champions 
                        if champ not in boosted_Mythic_champs and  champ != banner_Mythic_champ #just in case is added to banner_Mythic_champ but it SHOULD not happen
                    ]
                    selected = random.choice(pool)
                non_banner_Mythics_since_last += 1
                extra_shards = get_extra_shards(numbers_of_non_banner_mysthic_pulls)
                numbers_of_non_banner_mysthic_pulls += 1

        results[selected] += 1
        history.append(('Mythic', selected, extra_shards))

    elif rarity == 'Legendary':
        legendary_pity = 0
        if random.random() < 0.5:
            selected = random.choice(legendary_champions)
        else:
            selected = random.choice(legendary_legacy)

        results[selected] += 1
        history.append(('Legendary', selected, 0))
    else:
        if random.random() < 0.5:
            selected = random.choice(epic_champions)
        else:
            selected = random.choice(epic_legacy)
        results[selected] += 1
        history.append(('Epic', selected, 0))

    return selected,rarity,extra_shards
def multi_draw(n=100,show_output=False): #extra shards updated
    global results, history
    count_extra_shards = 0 
    results = Counter()
    history = []
    for _ in range(n):
        draw()

    category_totals = Counter({'Mythic': 0, 'Legendary': 0, 'Epic': 0})
    for rarity, _, extra in history:
        category_totals[rarity] += 1
        count_extra_shards += extra

    return results, history, category_totals, {
        "Mythic pity reset at": mythic_pity,
        "Legendary pity reset at": legendary_pity,
        "Boosted Mysthic Champs": boosted_Mythic_champs,
        "Banner Mythic Champion": banner_Mythic_champ,
        "Banner extra shards": count_extra_shards,
    }
def simulate_multiple_sessions(
        num_sessions=1,
        pulls_per_session=100,
        show_output=True,
        m_pity=None, l_pity=None,
        pity_banner=None,
        non_limited_Mythics_in_current_banned=None,
        stop_flag=lambda: True,   # cancel
        progress_callback=None #Progress bar
          ):

    global mythic_pity, legendary_pity, non_banner_Mythics_since_last
    global forced_Mythic_count, forced_banner_Mythic_count, banner_Mythic_champ, numbers_of_non_banner_mysthic_pulls

    # fallback: use session parameters if not provided
    m_pity = session_params[0]
    l_pity = session_params[1]
    pity_banner = session_params[2]
    non_limited_Mythics_in_current_banned = session_params[3]

    aggregate_results = Counter()
    aggregate_category_totals = Counter()
    banner_counts = []
    aggregate_extra_shards = 0
    total_forced_Mythics = 0
    total_forced_banner_Mythics = 0
    all_history = []
    last_metadata = None

    stats_lines = []  # <-- Accumulate output here

    for i in range(num_sessions):
        if not stop_flag():
            break  # Cancel early

         # --- Update progress ---
        if progress_callback:
            pct = int((i / num_sessions) * 100)
            progress_callback(pct)

        mythic_pity = m_pity
        legendary_pity = l_pity
        non_banner_Mythics_since_last = pity_banner
        forced_Mythic_count = 0
        forced_banner_Mythic_count = 0
        numbers_of_non_banner_mysthic_pulls = non_limited_Mythics_in_current_banned

        # One session
        results, session_history, category_totals, metadata = multi_draw(pulls_per_session)
        total_extra = sum(extra for _, _, extra in session_history)

        all_history.extend(session_history)
        last_metadata = metadata
        total_forced_Mythics += forced_Mythic_count
        total_forced_banner_Mythics += forced_banner_Mythic_count
        aggregate_results += results
        aggregate_category_totals += category_totals
        aggregate_extra_shards += total_extra
        banner_counts.append(results.get(banner_Mythic_champ, 0))
    if progress_callback:
        progress_callback(100)
    # --- Build stats text ---
    if num_sessions == 1:
        stats_lines.append(get_metadata(last_metadata))  # get key metadata
        stats_lines.append(get_breakdown_text(True))
    else:
        stats_lines.append("\nLegendary+ Items Pulled:")
        legendary_plus_items = {
            item: count for item, count in aggregate_results.items()
            if count > 0 and (
                item in Mythic_champions or item in Mythic_legacy or
                item in legendary_champions or item in legendary_legacy or item == banner_Mythic_champ
            )
        }
        for item, count in sorted(legendary_plus_items.items(), key=lambda x: x[1], reverse=True):
            stats_lines.append(f"{item}: {count}")

        stats_lines.append("\nAverage per session:")
        stats_lines.append(f"  Mythic: {aggregate_category_totals['Mythic']} total → {aggregate_category_totals['Mythic'] / num_sessions:.2f} per session")
        stats_lines.append(f"  Legendary: {aggregate_category_totals['Legendary']} total → {aggregate_category_totals['Legendary'] / num_sessions:.2f} per session")
        stats_lines.append(f"  Epic: {aggregate_category_totals['Epic']} total → {aggregate_category_totals['Epic'] / num_sessions:.2f} per session")
        stats_lines.append(f"  Average pulls of the Banner Mythic Champion per session: {sum(banner_counts)} total → {sum(banner_counts) / num_sessions:.2f} per session")
        stats_lines.append(f"  Average extra Banner Mythic Champion shards per session: {aggregate_extra_shards} total → {aggregate_extra_shards / num_sessions:.2f} per session")
        stats_lines.append(f"  Average forced Mythic pulls from pity per session: {total_forced_Mythics} total → {total_forced_Mythics / num_sessions:.2f}")
        stats_lines.append(f"  Forced Banner Mythic: {total_forced_banner_Mythics} total → {total_forced_banner_Mythics / num_sessions:.2f}")
    #if show_output:
        #print(stats_lines)
    clean()

    # Return results + stats text
    return (
        aggregate_results,
        aggregate_category_totals,
        total_forced_Mythics,
        total_forced_banner_Mythics,
        all_history,
        last_metadata,
        "\n".join(stats_lines)  # <-- the full statistics text
    )
def count_pulled():
    legendary_total = 0
    Mythic_total = 0
    epic_total = 0

    # Count Mythic champions and legacy
    for item, count in results.items():
        if item in legendary_champions or item in legendary_legacy:
            legendary_total += count
        elif item in Mythic_champions or item in Mythic_legacy or item==banner_Mythic_champ :
            Mythic_total += count
        elif item in epic_champions or item in epic_legacy:
            epic_total += count
    return epic_total,legendary_total,Mythic_total
def shard_tracking(history, repeats=1):#Adapted for GUI
    
    shards = {
        'Mythic': 0,
        'Mythic_banner': 0,
        'Mythic_non_banner': 0,
        'Mythic_extra': 0,
        'Legendary': 0,
        'Epic': 0,
        'Total': 0
    }

    legacy_pieces = {
        'Mythic': 0,
        'Legendary': 0,
        'Epic': 0
    }

    banner_shard = 40
    normal_shard = 10

    text_lines = []

    for entry in history:
        if len(entry) == 3:
            rarity, item, extra = entry
        elif len(entry) == 2:
            rarity, item = entry
            extra = 0

        if rarity == 'Mythic':
            if item == banner_Mythic_champ:
                shards['Mythic_banner'] += banner_shard
                shards['Mythic'] += banner_shard
            elif item in Mythic_champions:
                shards['Mythic_non_banner'] += normal_shard
                shards['Mythic_extra'] += extra
                shards['Mythic_banner'] += extra
                shards['Mythic'] += normal_shard + extra
            elif item in Mythic_legacy:
                legacy_pieces['Mythic'] += 1
                shards['Mythic_extra'] += extra

        elif rarity == 'Legendary':
            if item in legendary_champions:
                shards['Legendary'] += 10
            elif item in legendary_legacy:
                legacy_pieces['Legendary'] += 1

        elif rarity == 'Epic':
            if item in epic_champions:
                shards['Epic'] += 1
            elif item in epic_legacy:
                legacy_pieces['Epic'] += 1

    # --- Build the output text ---
    text_lines.append("\nShard Average:")
    text_lines.append(f"  Mythic Shards: {shards['Mythic_non_banner'] / repeats:.2f} non-banner + "
                      f"{shards['Mythic_banner'] / repeats:.2f} banner + "
                      f"{shards['Mythic_extra'] / repeats:.2f} extra = "
                      f"{shards['Mythic'] / repeats:.2f} total")
    text_lines.append(f"  Legendary Shards: {shards['Legendary'] / repeats:.2f}")
    text_lines.append(f"  Epic Shards: {shards['Epic'] / repeats:.2f} (converted from Epic Champions)")

    text_lines.append("\nLegacy Pieces Average:")
    text_lines.append(f"  Mythic Legacy Pieces: {legacy_pieces['Mythic'] / repeats:.2f}")
    text_lines.append(f"  Legendary Legacy Pieces: {legacy_pieces['Legendary'] / repeats:.2f}")
    text_lines.append(f"  Epic Legacy Pieces: {legacy_pieces['Epic'] / repeats:.2f}")

    return "\n".join(text_lines)
def get_lower_threshold(value, thresholds):#OK
    """
    Find the closest lower or equal threshold.
    thresholds: list of (threshold_value, name) tuples sorted ascending by threshold_value.
    Returns the (threshold_value, name) tuple or (0, "Below Unlocked") if none found.
    """
    valid = [(t, name) for t, name in thresholds if t <= value]
    if not valid:
        return (0, "Locked")
    return max(valid, key=lambda x: x[0])
def count_pulls_to_target(shards_needed): #OK
    global mythic_pity, legendary_pity
    shards = 0
    pulls = 0
    while shards < shards_needed:
        selected, rarity,extra = draw()
        pulls += 1
        if selected == banner_Mythic_champ:
            shards += 40
        else:
            shards += extra
    clean()
    return pulls
def avg_pulls_for_shards(simulations=1000, shards_needed=100,output=False):#Adapted for GUI
    global mythic_pity, legendary_pity,non_banner_Mythics_since_last,numbers_of_non_banner_mysthic_pulls
    total = 0
    min_pulls = float('inf')
    max_pulls = 0
    pulls_list = []  # store results of each simulation
    
    m_pity = session_params[0]
    l_pity = session_params[1]
    pity_banner = session_params[2]
    non_limited_Mythics_in_current_banned = session_params[3]
    
    for _ in range(simulations):
        mythic_pity = m_pity
        legendary_pity = l_pity
        non_banner_Mythics_since_last = pity_banner
        numbers_of_non_banner_mysthic_pulls = non_limited_Mythics_in_current_banned
        pulls = count_pulls_to_target(shards_needed)
        pulls_list.append(pulls)  # collect this run’s pulls
        total += pulls
        if pulls > max_pulls:
            max_pulls = pulls
        if pulls < min_pulls:
            min_pulls = pulls
    if output:
        print(f"\nAverage: {total / simulations}\nMin: {min_pulls}\nMax: {max_pulls}")
    clean()
    return (total / simulations),min_pulls,max_pulls,pulls_list
def label_to_stars(label):
    if label.lower() in ("locked", "unlocked"):
        return label
    match = re.match(r"(\d+)\s+(\w+)", label)
    if match:
        n = int(match.group(1))
        color = match.group(2).capitalize()
        return f"{color} {'★' * n}"
    return label  # fallback
def label_to_color(label):
    label = label.lower()
    if "white" in label:
        return "#dddddd"
    if "blue" in label:
        return "#5fa8d3"
    if "purple" in label:
        return "#b186f5"
    if "gold" in label:
        return "#ffd700"
    if "red" in label:
        return "#ff4c4c"
    if "unlocked" in label:
        return "#a0a0a0"
    return "#888888"
def plot_multiple_shard_distributions_banner(shard_arrays, titles=None, starting_shards_list=None):#Adapted for GUI
    n = len(shard_arrays) #On GUI should be always 1
    if n > 4:
        print("Maximum of 4 distributions supported.")
        return

    if titles is None:
        titles = [f"Distribution {i+1}" for i in range(n)]
    if starting_shards_list is None:
        starting_shards_list = [0] * n

    cols = min(n, 2)
    rows = math.ceil(n / cols)
    fig_width = max(10, 6 * cols)

    fig, axes = plt.subplots(rows, cols, figsize=(fig_width, 5 * rows), squeeze=False)

    for idx, (shard_array,title, starting_shards) in enumerate(zip(shard_arrays, titles,starting_shards_list)):
        row = idx // cols
        col = idx % cols
        ax = axes[row][col]

        adjusted_shard_array = shard_array + starting_shards

        # Threshold intervals
        thresholds = sorted(SHARD_THRESHOLDS, key=lambda x: x[0])
        intervals, labels = [], []
        prev = 0
        prev_label = "Locked"
        for threshold, label in thresholds:
            intervals.append((prev, threshold - 1))
            labels.append(prev_label)
            prev = threshold
            prev_label = label
        intervals.append((prev, adjusted_shard_array.max()))
        labels.append(prev_label)

        # Bin counts
        counts = []
        for low, high in intervals:
            count = np.sum((adjusted_shard_array >= low) & (adjusted_shard_array <= high))
            counts.append(count)

        total = sum(counts)
        filtered = [(label, count) for label, count in zip(labels, counts) if count > 0]
        if not filtered:
            ax.set_title("No data")
            continue

        filtered_labels, filtered_counts = zip(*filtered)
        percentages = [count / total * 100 for count in filtered_counts]
        star_labels = [label_to_stars(lbl) for lbl in filtered_labels]
        colors = [label_to_color(lbl) for lbl in filtered_labels]

        bars = ax.bar(star_labels, percentages, color=colors, edgecolor='black')

        # Tooltip
        cursor = mplcursors.cursor(bars, hover=True)
        @cursor.connect("add")
        def on_add(sel):
            label = filtered_labels[sel.index]
            count = filtered_counts[sel.index]
            percent = percentages[sel.index]
            sel.annotation.set(text=f"{label}\n{count} times\n{percent:.2f}%")
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

        ax.set_xticks(range(len(star_labels)))
        ax.set_xticklabels(star_labels, rotation=45, ha='right')
        ax.set_ylabel('Percentage (%)')
        ax.set_title(title)

    plt.tight_layout()
    plt.show()
def format_shard_distribution_title(pulls_limit, current_shards=0, m_pity=0, l_pity=0, non_banner=0, non_limited_Mythics_in_current_banned=0):
    base = f"Shard Count Distribution\n{pulls_limit} pulls"
    if current_shards > 0:
        base += f", Current shards: {current_shards}"

    extras = []
    if m_pity > 0:
        extras.append(f"Mythic Pity: {m_pity}")
    if l_pity > 0:
        extras.append(f"Legendary Pity: {l_pity}")
    if non_banner > 0:
        extras.append(f"Non-Banner Since Last: {non_banner}")
    if non_limited_Mythics_in_current_banned > 0:
        extras.append(f"Non-Limited Mythics Pulled: {non_limited_Mythics_in_current_banned}")

    if extras:
        base += "\n" + ", ".join(extras)
    return base
def plot_multiple_Mythic_distributions(arrays, pull_limits, chart_type=1):
    """
    arrays: list of tuples (non_banner_array, banner_array, extra_array)
    chart_type:
        1 = non-banner only
        2 = banner only
        3 = extra shards
    """
    n = len(arrays)
    cols = min(n, 2)
    rows = math.ceil(n / cols)
    fig_width = max(10, 6 * cols)

    if chart_type == 1:
        arr_idx, color, title_prefix = 0, 'lightgreen', 'Mythics'
    elif chart_type == 2:
        arr_idx, color, title_prefix = 1, 'darkred', 'Banner Mythics'
    elif chart_type == 3:
        arr_idx, color, title_prefix = 2, 'skyblue', 'Extra Banner Shards'
    else:
        raise ValueError("Invalid chart_type")

    fig, axes = plt.subplots(rows, cols, figsize=(fig_width, 5 * rows), squeeze=False)

    for idx, pulls_limit in enumerate(pull_limits):
        row = idx // cols
        col = idx % cols
        data_array = arrays[idx][arr_idx]
        ax = axes[row][col]

        unique, counts = np.unique(data_array, return_counts=True)
        total = counts.sum()
        percentages = (counts / total) * 100
        labels = [f"{val}" for val in unique]

        bars = ax.bar(unique, percentages, color=color, edgecolor='black')
        ax.set_title(f"{pulls_limit} pulls ({title_prefix})")
        ax.set_xlabel("Shards / Pulls")
        ax.set_ylabel("Frequency (%)")
        ax.set_xticks(unique)
        ax.tick_params(axis='x', rotation=90)

        cursor = mplcursors.cursor(bars, hover=True)
        @cursor.connect("add")
        def on_add(sel, labels=labels, counts=counts, percentages=percentages):
            idx_sel = sel.index
            label = labels[idx_sel]
            count = counts[idx_sel]
            percent = percentages[idx_sel]
            sel.annotation.set(text=f"{label}\n{count} times\n{percent:.2f}%")
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

    # Hide unused subplots
    for idx_unused in range(len(pull_limits), rows * cols):
        row = idx_unused // cols
        col = idx_unused % cols
        fig.delaxes(axes[row][col])

    plt.tight_layout()
    fig.canvas.manager.set_window_title(title_prefix)
    plt.show(block=False)
def prob_mythic_pull1(#Adpted for GUI
    pulls_list,
    simulations=10000,
    m_pity=None,
    l_pity=None,
    pity_banner=None,
    non_limited_Mythics_in_current_banned=None,
    stop_flag=lambda: True,           # <-- cancel support
    progress_callback=None            # <-- progress updates
):
    """
    runs the Mythic-pull simulation for each pull_limit in pulls_list
    and plots them side by side.

    pulls_list: either a list of ints, or a comma-separated string e.g. "50,100,150"
    """

    result_text = []
    m_pity = session_params[0]
    l_pity = session_params[1]
    pity_banner = session_params[2]
    non_limited_Mythics_in_current_banned = session_params[3]

    total_iterations = sum(pulls_limit * simulations for pulls_limit in pulls_list)
    completed = 0
    # parse pulls_list into a list of ints
    if isinstance(pulls_list, str):
        pull_limits = [int(x.strip()) for x in pulls_list.split(",") if x.strip().isdigit()]
    else:
        pull_limits = list(pulls_list)

    n = len(pull_limits)
    if n == 0:
        print("No valid pull limits provided.")
        return
    if n > 4:
        print("Can only plot up to 4 distributions at once.")
        pull_limits = pull_limits[:4]
        n = 4

    # run sims for each pull_limit, collect raw Mythic-pull arrays
    all_arrays = []
    for pulls_limit in pull_limits:
        mythic_counts = defaultdict(int)
        banner_counts = defaultdict(int)
        banner_flat = []
        Mythic_flat = []
        text_lines = []

        global mythic_pity, legendary_pity, non_banner_Mythics_since_last, numbers_of_non_banner_mysthic_pulls
        for _ in range(simulations):
            mythic_pity = m_pity
            legendary_pity = l_pity
            non_banner_Mythics_since_last = pity_banner
            numbers_of_non_banner_mysthic_pulls = non_limited_Mythics_in_current_banned

            pulls = 0
            Mythic_count = 0
            banner_Mythic_count = 0
            while pulls < pulls_limit:
                if not stop_flag():
                    # Cancel requested
                    return None  # or raise an exception if you prefer
                res = draw()
                if res is None:
                    continue
                selected, rarity, _ = res
                pulls += 1
                if rarity == "Mythic":
                    Mythic_count += 1
                    if selected in banner_Mythic_champions:
                        banner_Mythic_count += 1
                completed += 1
                if progress_callback:
                    # Multiply by 100 to get percentage
                    progress_callback(int((completed / total_iterations) * 100))

            banner_counts[banner_Mythic_count] += 1
            mythic_counts[Mythic_count] += 1
            Mythic_flat.extend([Mythic_count])
            banner_flat.extend([banner_Mythic_count])
        all_arrays.append((np.array(Mythic_flat), np.array(banner_flat)))
        # Add header
        text_lines.append(f"\nNon-banner Mythic Pulls over {simulations} simulations with {pulls_limit} pulls:")
        total = sum(mythic_counts.values())

        # Table header
        text_lines.append(f"\n{'Mythics':>8}  {'Chance':>8}  {'At Least':>10}")
        text_lines.append("-" * 35)

        # Table rows
        remaining = 1.0
        for mythics, count in sorted(mythic_counts.items()):  # Sort by number of non-banner Mythics
            probability = count / total
            text_lines.append(f"{mythics:>8}  {probability:8.2%}  {remaining:10.2%}")
            remaining -= probability

        # Convert list of lines to a single string
        #result_text.append(text_lines)
        result_text.append("\n".join(text_lines)) 
    #plot_multiple_Mythic_distributions(all_arrays,pull_limits)
    clean()
    return result_text,all_arrays,pull_limits
def run_shard_simulations(
    simulations=1000,
    shard_targets=None,
    stop_flag=lambda: True,       # stop flag for cancellation
    progress_callback=lambda val: None  # progress updates
):
    global  mythic_pity, legendary_pity, non_banner_Mythics_since_last, numbers_of_non_banner_mysthic_pulls,session_params
    if shard_targets is None:
        shard_targets = [80, 120]
    #print(f"({session_params[0]} , {session_params[1]} , {session_params[2]} , {session_params[3]})")
    values = []
    text_lines = []
    text_lines.append("\nSimulation Results Table:")
    text_lines.append(f"{'Shards':>6} | {'Avg Pulls':>10} | {'Min Pulls':>10} | {'Max Pulls':>10}")
    text_lines.append("-" * 48)

    for target in shard_targets:
        if not stop_flag():
            text_lines.append("\n⚠️ Simulation cancelled by user.")
            break

        pull_counts = []

        for _ in range(simulations):
            mythic_pity = session_params[0]
            legendary_pity = session_params[1]
            non_banner_Mythics_since_last = session_params[2]
            numbers_of_non_banner_mysthic_pulls = session_params[3]

            if not stop_flag():
                # Cancel mid-simulation
                text_lines.append("\n⚠️ Simulation cancelled by user.")
                break

            pulls_needed = 0
            shards_accum = 0
            while shards_accum < target:
                # Simulate a single pull
                selected, rarity, extra = draw()
                pulls_needed += 1
                #print(f"({mythic_pity} , {legendary_pity} , {non_banner_Mythics_since_last} , {numbers_of_non_banner_mysthic_pulls})")
                if rarity == "Mythic" and selected in banner_Mythic_champions:
                    shards_accum += 40
                    shards_accum += extra
            #print(f"Sim. {i} DONE")

            pull_counts.append(pulls_needed)

        if pull_counts:
            avg_pulls = np.mean(pull_counts)
            min_pulls = min(pull_counts)
            max_pulls = max(pull_counts)
        else:
            avg_pulls = min_pulls = max_pulls = 0

        values.append((target, avg_pulls, min_pulls, max_pulls, pull_counts))
        text_lines.append(f"{target:>6} | {avg_pulls:10.3f} | {min_pulls:10} | {max_pulls:10}")

    clean()
    return "\n".join(text_lines), values, shard_targets
def show_pulls_for_shards(values): #works on GUI
    for row in values:
        target, avg, min_pulls, max_pulls, pull_list = row
        pulls = np.array(pull_list)
        median = np.median(pulls)
        q1 = np.percentile(pulls, 25)
        q3 = np.percentile(pulls, 75)
        std_dev = np.std(pulls)
        skew = ((pulls - avg)**3).mean() / (std_dev**3)
        kurtosis = ((pulls - avg)**4).mean() / (std_dev**4) - 3

        plt.figure(figsize=(10, 6))

        # Scatter all raw pulls
        scatter = plt.scatter(range(len(pulls)), pulls, alpha=0.4, s=10, c="red", label="Raw Pulls")

        # Lines for stats
        plt.axhline(y=avg, color="blue", linestyle="-", label=f"Average: {avg:.2f}")
        plt.axhline(y=median, color="purple", linestyle=":", label=f"Median: {median}")
        plt.axhline(y=q1, color="cyan", linestyle="--", label=f"Q1: {q1}")
        plt.axhline(y=q3, color="cyan", linestyle="--", label=f"Q3: {q3}")
        plt.axhline(y=min_pulls, color="green", linestyle="--", label=f"Min: {min_pulls}")
        plt.axhline(y=max_pulls, color="orange", linestyle="--", label=f"Max: {max_pulls}")

        # Shaded bands
        plt.fill_between([0, len(pulls)], avg - std_dev, avg + std_dev, color="green", alpha=0.2, label=f"Std Dev: {std_dev:.2f}")
        plt.fill_between([0, len(pulls)], q1, q3, color="blue", alpha=0.2, label=f"IQR (Q1–Q3): {q1:.2f}-{q3:.2f}")

        plt.xlabel("Simulation Run")
        plt.ylabel("Number of Pulls")
        plt.title(f"Pulls Distribution for {target} Shards\n"
                  f"Skewness: {skew:.2f} (Positive → More pulls above average)\n"
                  f"Kurtosis: {kurtosis:.2f} (Positive → More extreme values)")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()

        # Interactive tooltip for raw points
        cursor = mplcursors.cursor(scatter, hover=True)
        @cursor.connect("add")
        def on_add(sel):
            sel.annotation.set_text(f"Pull: {pulls[sel.index]}")

        plt.show()
        # Print probability table if requested 
def prob_tbl_txt(values, success_thresholds):
    text_lines = []

    prob = []
    for row in values:
        _, _, _, _, pull_list = row
        pulls = np.array(pull_list)
        prob_success = {}
        if success_thresholds:
            for x in success_thresholds:
                prob_success[x] = np.mean(pulls <= x)
            prob.append(prob_success)

    if not prob:
        return ["No success thresholds provided."]

    # Collect all unique pull thresholds
    pull_thresholds = sorted({x for prob_success in prob for x in prob_success.keys()})

    # Build the table
    table_data = {}
    for i, target in enumerate([row[0] for row in values]):
        prob_success = prob[i]
        table_data[target] = [prob_success.get(p, 0) * 100 for p in pull_thresholds]

    df = pd.DataFrame(table_data, index=pull_thresholds)
    df.index.name = "Pulls ≤ X"

    # Add table to text_lines
    text_lines.append("\nProbability of Success Table (%):")
    text_lines.extend(df.to_string(float_format="{:6.2f}".format).split("\n"))

    return text_lines
def set_draws(filename):
    import random
    from collections import Counter

    global results, history

    results = Counter()
    history = []
    custom_epic_piece = {"Legacy Weapon"}
    custom_epic_champ = {"AC/DC Shard"}
    # Forced / pity counters
    forced_mythic = 0
    banner_normal = 0  # Banner Mythic obtained normally
    forced_banner  = 0
    forced_legendary = 0
    mythic_pity = 0
    legendary_pity = 0
    non_banner_counter = 0    # Counts non-banner mythics since last banner

    # Lowercase pools for comparison
    legendary_legacy_lower = [x.lower() for x in legendary_legacy]
    Mythic_champions_lower = [x.lower() for x in Mythic_champions]
    Mythic_legacy_lower = [x.lower() for x in Mythic_legacy]
    boosted_Mythic_champs_lower = [x.lower() for x in boosted_Mythic_champs]
    banner_Mythic_champions_lower = [x.lower() for x in banner_Mythic_champions]
    legendary_champions_lower = [x.lower() for x in legendary_champions]
    epic_champions_lower = [x.lower() for x in epic_champions]
    epic_legacy_lower = [x.lower() for x in epic_legacy]
    custom_epic_piece_lower = [x.lower() for x in custom_epic_piece]
    custom_epic_champ_lower = [x.lower() for x in custom_epic_champ]

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            champ = line.strip()
            if not champ or champ.startswith("#"):
                continue
            champ_lower = champ.lower()

            mythic_pity += 1
            legendary_pity += 1

            if champ_lower in custom_epic_piece_lower:
                rarity = "Epic"
                champ = random.choice(epic_legacy)
            elif champ_lower in custom_epic_champ_lower:
                champ = random.choice(epic_champions)
                rarity = "Epic"
                
            elif champ_lower in Mythic_champions_lower or champ_lower in Mythic_legacy_lower or champ_lower in boosted_Mythic_champs_lower:
                rarity = "Mythic"
                non_banner_counter += 1

                if mythic_pity >= 50:
                    forced_mythic += 1   # forced due to pity

                # reset counters
                legendary_pity = 0
                mythic_pity = 0

            elif champ_lower in banner_Mythic_champions_lower:
                rarity = "Mythic"
                if non_banner_counter >= 3:
                    forced_banner += 1
                else:
                    banner_normal += 1
                mythic_pity = 0
                legendary_pity = 0
                non_banner_counter = 0

            elif champ_lower in legendary_champions_lower or champ_lower in legendary_legacy_lower:
                rarity = "Legendary"
                if legendary_pity >= 10:
                    forced_legendary += 1
                legendary_pity = 0

            elif champ_lower in epic_champions_lower or champ_lower in epic_legacy_lower:
                rarity = "Epic"

            else:
                rarity = "Unknown"

            results[champ] += 1
            history.append((rarity, champ, 0))

    # Totals by rarity
    category_totals = Counter({'Mythic': 0, 'Legendary': 0, 'Epic': 0})
    for rarity, _, _ in history:
        category_totals[rarity] += 1

    # Top 5 most common Mythics and Legendaries
    from itertools import chain
    epic_only = {k: v for k, v in results.items() if k.lower() in 
                    [x.lower() for x in chain(epic_champions, epic_legacy)]}
    mythics_only = {k: v for k, v in results.items() if k.lower() in 
                    [x.lower() for x in chain(Mythic_champions, Mythic_legacy, boosted_Mythic_champs)]}
    banner_only = {k: v for k, v in results.items() if k.lower() in 
                    [x.lower() for x in chain(banner_Mythic_champions)]}

    legendaries_only = {k: v for k, v in results.items() if k.lower() in
                        [x.lower() for x in chain(legendary_champions, legendary_legacy)]}
    top5_mythics = Counter(mythics_only).most_common(5)
    top5_legendaries = Counter(legendaries_only).most_common(5)
    # Average pulls per Mythic and Banner
    mythic_indices = [i for i, (r, _, _) in enumerate(history) if r == "Mythic"]
    banner_indices = [i for i, (r, champ, _) in enumerate(history) if champ.lower() in banner_Mythic_champions_lower]

    avg_pulls_mythic = (sum((mythic_indices[i] - mythic_indices[i-1] for i in range(1, len(mythic_indices)))) / len(mythic_indices[1:])) if len(mythic_indices) > 1 else len(history)
    avg_pulls_banner = (sum((banner_indices[i] - banner_indices[i-1] for i in range(1, len(banner_indices)))) / len(banner_indices[1:])) if len(banner_indices) > 1 else len(history)

    epic_champ = {k: v for k, v in results.items() if k.lower() in 
                    [x.lower() for x in chain(epic_champions)]}
    epic_piece = {k: v for k, v in results.items() if k.lower() in 
                    [x.lower() for x in chain(epic_legacy)]}
    mythics_champ = {k: v for k, v in results.items() if k.lower() in 
                    [x.lower() for x in chain(Mythic_champions, boosted_Mythic_champs)]}
    mythics_piece = {k: v for k, v in results.items() if k.lower() in 
                    [x.lower() for x in chain(Mythic_legacy)]}
    banner_only = {k: v for k, v in results.items() if k.lower() in 
                    [x.lower() for x in chain(banner_Mythic_champions)]}

    legendaries_champ = {k: v for k, v in results.items() if k.lower() in
                        [x.lower() for x in chain(legendary_champions)]}
    legendaries_piece = {k: v for k, v in results.items() if k.lower() in
                        [x.lower() for x in chain(legendary_legacy)]}
    # Epic
    epic_champ_count = sum(epic_champ.values())
    epic_piece_count = sum(epic_piece.values())

    # Mythic
    mythics_champ_count = sum(mythics_champ.values())
    mythics_piece_count = sum(mythics_piece.values())
    banner_only_count = sum(banner_only.values())

    # Legendary
    legendaries_champ_count = sum(legendaries_champ.values())
    legendaries_piece_count = sum(legendaries_piece.values())

    return results, history, category_totals, {
        "Mythic pity reset at": mythic_pity,
        "Legendary pity reset at": legendary_pity,
        "Forced Mythics": forced_mythic,
        "Forced Banner": forced_banner,
        "Normal Banner": banner_normal,
        "Forced Legendary": forced_legendary,
        "Top 5 Mythics": top5_mythics,
        "Top 5 Legendaries": top5_legendaries,
        "Banner Pulls": banner_only,
        "Average pulls per banner": avg_pulls_banner,
        "Average pulls per mythic": avg_pulls_mythic,
        "Pulls Count Epic":epic_only,
        "Pulls Count Legendary": legendaries_only,
        "Pulls Count Mythic": mythics_only,
        "Epic Piece Count": epic_piece_count,
        "Epic Champion Count": epic_champ_count,
        "Legendary Piece Count": legendaries_piece_count,
        "Legendary Champion Count":legendaries_champ_count,
        "Mythic Piece Count": mythics_piece_count,
        "Mythic Champion Count": mythics_champ_count,
        "Banner Champion Count":banner_only_count

    }
def get_breakdown_text(epics=False):#OK
    """Build breakdown text for results panel"""
    global results, history  

    text_lines = []

    temp_list = Mythic_champions.copy()
    if banner_Mythic_champ not in temp_list:
        temp_list.append(banner_Mythic_champ)

    # Totals
    epic_total, legendary_total, mythic_total = count_pulled()
    text_lines.append("\nSTATS:")
    text_lines.append(f"Legendary: {legendary_total}")
    text_lines.append(f"Mythic: {mythic_total} (Banner {results.get(banner_Mythic_champ, 0)}x)")
    text_lines.append(f"Epic: {epic_total}")

    # Shards
    shards = sum(extra for entry in history if len(entry) == 3 for extra in [entry[2]])
    text_lines.append(f"Extra {banner_Mythic_champ} shards: {shards}")

    # Mythic Champions
    mythic_champ_entries = [
        f"  {name}: {results.get(name, 0)}"
        for name in sorted(temp_list, key=lambda x: results.get(x, 0), reverse=True)
        if results.get(name, 0) > 0
    ]
    if mythic_champ_entries:
        text_lines.append("\nMythic Champions:")
        text_lines.extend(mythic_champ_entries)

    # Mythic Legacy
    mythic_legacy_entries = [
        f"  {name}: {results.get(name, 0)}"
        for name in sorted(Mythic_legacy, key=lambda x: results.get(x, 0), reverse=True)
        if results.get(name, 0) > 0
    ]
    if mythic_legacy_entries:
        text_lines.append("\nMythic Legacy Pieces:")
        text_lines.extend(mythic_legacy_entries)

    # Legendary Champions
    legendary_champ_entries = [
        f"  {name}: {results.get(name, 0)}"
        for name in sorted(legendary_champions, key=lambda x: results.get(x, 0), reverse=True)
        if results.get(name, 0) > 0
    ]
    if legendary_champ_entries:
        text_lines.append("\nLegendary Champions:")
        text_lines.extend(legendary_champ_entries)

    # Legendary Legacy
    legendary_legacy_entries = [
        f"  {name}: {results.get(name, 0)}"
        for name in sorted(legendary_legacy, key=lambda x: results.get(x, 0), reverse=True)
        if results.get(name, 0) > 0
    ]
    if legendary_legacy_entries:
        text_lines.append("\nLegendary Legacy Pieces:")
        text_lines.extend(legendary_legacy_entries)
    if (epics):
        # Epics
        epic_champ_entries = [
            f"  {name}: {results.get(name, 0)}"
            for name in sorted(epic_champions, key=lambda x: results.get(x, 0), reverse=True)
            if results.get(name, 0) > 0
        ]
        if epic_champ_entries:
            text_lines.append("\nEpic Champions:")
            text_lines.extend(epic_champ_entries)

        epic_legacy_entries = [
            f"  {name}: {results.get(name, 0)}"
            for name in sorted(epic_legacy, key=lambda x: results.get(x, 0), reverse=True)
            if results.get(name, 0) > 0
        ]
        if epic_legacy_entries:
            text_lines.append("\nEpic Legacy Pieces:")
            text_lines.extend(epic_legacy_entries)

    # ✅ Return instead of print
    return "\n".join(text_lines)
def get_metadata(last_metadata, ignored_keys=None):
    if ignored_keys is None:
        ignored_keys = {}

    text_lines = []
    if last_metadata:
        for key, value in last_metadata.items():
            if key not in ignored_keys:
                line = f"{key}: {value}"
                text_lines.append(line)   # collect lines
                print(line)               # optional: still print to console

    return "\n".join(text_lines)
def prob_banner_pull(
    pulls_list="1040",
    simulations=10000,
    m_pity=None,
    l_pity=None,
    pity_banner=None,
    non_limited_Mythics_in_current_banned=None,
    current_shards=0,
    stop_flag=lambda: True,           # <-- cancel support
    progress_callback=None            # <-- progress updates
):
    if isinstance(pulls_list, str):
        pulls_list = [int(x.strip()) for x in pulls_list.split(",") if x.strip().isdigit()]
    if not pulls_list:
        return "No valid pull values provided."

    print_text = []
    list_of_results = []
    list_of_history = []
    all_arrays = []
    all_titles = []

    # Use session parameters as fallback
    m_pity = m_pity or session_params[0]
    l_pity = l_pity or session_params[1]
    pity_banner = pity_banner or session_params[2]
    non_limited_Mythics_in_current_banned = non_limited_Mythics_in_current_banned or session_params[3]

    total_iterations = sum(pulls_limit * simulations for pulls_limit in pulls_list)
    completed = 0

    for pulls_limit in pulls_list:
        shard_counts = defaultdict(int)
        shard_list = []
        text_lines = []

        cumulative_results = Counter()
        cumulative_history = []

        total_Mythic_pulls = 0
        total_limited_Mythic_pulls = 0

        for _ in range(simulations):

            # Reset session counters
            global mythic_pity, legendary_pity, non_banner_Mythics_since_last, numbers_of_non_banner_mysthic_pulls, results, history
            mythic_pity = m_pity
            legendary_pity = l_pity
            non_banner_Mythics_since_last = pity_banner
            numbers_of_non_banner_mysthic_pulls = non_limited_Mythics_in_current_banned
            results = Counter()
            history = []

            shards = 0
            pulls = 0
            sim_history = []

            while pulls < pulls_limit:
                if not stop_flag():
                    # Cancel requested
                    return None  # or raise an exception if you prefer
                res = draw()
                if res is None:
                    continue
                selected, rarity, extra = res
                pulls += 1
                cumulative_results[selected] += 1
                sim_history.append((rarity, selected, extra))
                if rarity == "Mythic":
                    total_Mythic_pulls += 1
                    if selected == banner_Mythic_champ:
                        total_limited_Mythic_pulls += 1
                        shards += 40
                    else:
                        shards += extra
                 # Update progress
                completed += 1
                if progress_callback:
                    # Multiply by 100 to get percentage
                    progress_callback(int((completed / total_iterations) * 100))

            threshold_bucket, _ = get_lower_threshold(shards + current_shards, SHARD_THRESHOLDS)
            shard_counts[threshold_bucket] += 1
            shard_list.append(shards)
            cumulative_history.extend(sim_history)

           

        list_of_results.append(cumulative_results)
        list_of_history.append(cumulative_history)

        shard_array = np.array(shard_list)
        all_arrays.append(shard_array)

        text_lines.append(f"\n--- Shards Distribution for {pulls_limit} pulls ({simulations} simulations) ---")
        if current_shards != 0:
            text_lines.append(f"------ Current Shards: {current_shards} ------")
        total = sum(shard_counts.values())
        text_lines.append(f"\n{'Shards':>6}  {'Chance':>8}  {'At Least':>10}")
        text_lines.append("-" * 40)
        remaining = 1.0
        for mythics, count in sorted(shard_counts.items()):
            probability = count / total
            text_lines.append(f"{mythics:>8}  {probability:8.2%}  {remaining:10.2%}")
            remaining -= probability

        avg_MYTHIC_RATE = total_Mythic_pulls / (pulls_limit * simulations)
        avg_limited_MYTHIC_RATE = total_limited_Mythic_pulls / (pulls_limit * simulations)
        expected_pulls_per_Mythic = (1 / avg_MYTHIC_RATE) if avg_MYTHIC_RATE > 0 else float('inf')
        expected_pulls_per_limited = (1 / avg_limited_MYTHIC_RATE) if avg_limited_MYTHIC_RATE > 0 else float('inf')

        text_lines.append("\n--- Summary Statistics ---")
        text_lines.append(f"Mean shards:     {np.mean(shard_array):.2f}")
        text_lines.append(f"Median:          {np.median(shard_array)}")
        text_lines.append(f"Q1 (25%):        {np.percentile(shard_array, 25)}")
        text_lines.append(f"Q3 (75%):        {np.percentile(shard_array, 75)}")
        text_lines.append(f"Min shards:      {np.min(shard_array)}")
        text_lines.append(f"Max shards:      {np.max(shard_array)}")
        text_lines.append(f"Std deviation:   {np.std(shard_array):.2f}")
        text_lines.append(f"Avg Mythic Pull Rate:         {avg_MYTHIC_RATE:.4%}")
        text_lines.append(f"Expected pulls per Mythic:    {expected_pulls_per_Mythic:.2f}")
        text_lines.append(f"Avg Limited Mythic Pull Rate: {avg_limited_MYTHIC_RATE:.4%}")
        text_lines.append(f"Expected pulls per Limited:   {expected_pulls_per_limited:.2f}")

        title = format_shard_distribution_title(
            pulls_limit, current_shards, m_pity, l_pity, pity_banner, non_limited_Mythics_in_current_banned
        )
        all_titles.append(title)
        print_text.append("\n".join(text_lines))

    clean()
    return print_text, all_arrays, all_titles, ([current_shards] * len(all_arrays)), list_of_results, list_of_history
def prob_mythic_pull(
    pulls_list,
    simulations=10000,
    m_pity=None,
    l_pity=None,
    pity_banner=None,
    non_limited_Mythics_in_current_banned=None,
    stop_flag=lambda: True,
    progress_callback=None
):
    """
    Runs Mythic pull simulations for each pull limit and generates tables for
    both non-banner Mythic pulls and banner Mythic pulls.
    """

    result_text = []
    m_pity = m_pity or session_params[0]
    l_pity = l_pity or session_params[1]
    pity_banner = pity_banner or session_params[2]
    non_limited_Mythics_in_current_banned = non_limited_Mythics_in_current_banned or session_params[3]

    # Parse pulls_list
    if isinstance(pulls_list, str):
        pull_limits = [int(x.strip()) for x in pulls_list.split(",") if x.strip().isdigit()]
    else:
        pull_limits = list(pulls_list)
    if not pull_limits:
        return None

    total_iterations = sum(p * simulations for p in pull_limits)
    completed = 0

    all_arrays = []

    for pulls_limit in pull_limits:
        mythic_counts = defaultdict(int)
        banner_counts = defaultdict(int)
        Mythic_flat = []
        banner_flat = []
        text_lines = []

        global mythic_pity, legendary_pity, non_banner_Mythics_since_last, numbers_of_non_banner_mysthic_pulls

        for _ in range(simulations):
            mythic_pity = m_pity
            legendary_pity = l_pity
            non_banner_Mythics_since_last = pity_banner
            numbers_of_non_banner_mysthic_pulls = non_limited_Mythics_in_current_banned

            pulls = 0
            Mythic_count = 0
            banner_Mythic_count = 0

            while pulls < pulls_limit:
                if not stop_flag():
                    return None  # Cancel requested
                res = draw()
                if res is None:
                    continue
                selected, rarity, _ = res
                pulls += 1
                if rarity == "Mythic":
                    Mythic_count += 1
                    if selected in banner_Mythic_champions:
                        banner_Mythic_count += 1

                # Update progress
                completed += 1
                if progress_callback:
                    progress_callback(int((completed / total_iterations) * 100))

            mythic_counts[Mythic_count] += 1
            banner_counts[banner_Mythic_count] += 1
            Mythic_flat.append(Mythic_count)
            banner_flat.append(banner_Mythic_count)

        all_arrays.append((np.array(Mythic_flat), np.array(banner_flat)))

        # --- Non-banner Mythic table ---
        text_lines.append(f"\nNon-banner Mythic Pulls over {simulations} simulations with {pulls_limit} pulls:")
        total = sum(mythic_counts.values())
        text_lines.append(f"\n{'Mythics':>8}  {'Chance':>8}  {'At Least':>10}")
        text_lines.append("-" * 35)
        remaining = 1.0
        for mythics, count in sorted(mythic_counts.items()):
            probability = count / total
            text_lines.append(f"{mythics:>8}  {probability:8.2%}  {remaining:10.2%}")
            remaining -= probability

        # --- Banner Mythic table ---
        text_lines.append(f"\nBanner Mythic Pulls over {simulations} simulations with {pulls_limit} pulls:")
        total_banner = sum(banner_counts.values())
        text_lines.append(f"\n{'Banner':>8}  {'Chance':>8}  {'At Least':>10}")
        text_lines.append("-" * 35)
        remaining_banner = 1.0
        for banner, count in sorted(banner_counts.items()):
            probability = count / total_banner
            text_lines.append(f"{banner:>8}  {probability:8.2%}  {remaining_banner:10.2%}")
            remaining_banner -= probability

        result_text.append("\n".join(text_lines))

    clean()
    return result_text, all_arrays, pull_limits
def prob_mythic_shards(
    pulls_list,
    simulations=10000,
    m_pity=None,
    l_pity=None,
    pity_banner=None,
    non_limited_Mythics_in_current_banned=None,
    stop_flag=lambda: True,
    progress_callback=None
):
    """
    Runs Mythic pull simulations for each pull limit and calculates
    total shards per simulation for both banner and non-banner Mythics.
    """

    result_text = []
    m_pity = m_pity or session_params[0]
    l_pity = l_pity or session_params[1]
    pity_banner = pity_banner or session_params[2]
    non_limited_Mythics_in_current_banned = non_limited_Mythics_in_current_banned or session_params[3]

    # Parse pulls_list
    if isinstance(pulls_list, str):
        pull_limits = [int(x.strip()) for x in pulls_list.split(",") if x.strip().isdigit()]
    else:
        pull_limits = list(pulls_list)
    if not pull_limits:
        return None

    total_iterations = sum(p * simulations for p in pull_limits)
    completed = 0

    all_arrays = []

    for pulls_limit in pull_limits:
        extra_banner_shards_list = []
        banner_pulls_list = []
        mythic_pulls_list = []
        text_lines = []

        global mythic_pity, legendary_pity, non_banner_Mythics_since_last, numbers_of_non_banner_mysthic_pulls

        for _ in range(simulations):
            mythic_pity = m_pity
            legendary_pity = l_pity
            non_banner_Mythics_since_last = pity_banner
            numbers_of_non_banner_mysthic_pulls = non_limited_Mythics_in_current_banned

            pulls = 0
            banner_shards = 0
            mythic_pulls = 0
            banner = 0

            while pulls < pulls_limit:
                if not stop_flag():
                    return None  # Cancel requested
                res = draw()
                if res is None:
                    continue
                selected, rarity, extra = res
                pulls += 1

                if rarity == "Mythic":
                    mythic_pulls += 1
                    if selected in banner_Mythic_champions:
                        banner += 1
                    else:                       
                        banner_shards += extra
                        

                # Update progress
                completed += 1
                if progress_callback:
                    progress_callback(int((completed / total_iterations) * 100))
           
            banner_pulls_list.append(banner)
            extra_banner_shards_list.append(banner_shards)
            mythic_pulls_list.append(mythic_pulls)

        all_arrays.append((np.array(mythic_pulls_list), np.array(banner_pulls_list),np.array(extra_banner_shards_list)))

        # --- Non-banner shards table ---
        text_lines.append(f"\nNon-banner Mythic Pulls over {simulations} simulations with {pulls_limit} pulls:")
        shards_counter = Counter(mythic_pulls_list)
        total_shards = sum(shards_counter.values())
        text_lines.append(f"\n{'Shards':>8}  {'Chance':>8}  {'At Least':>10}")
        text_lines.append("-" * 35)
        remaining = 1.0
        for shards, count in sorted(shards_counter.items()):
            probability = count / total_shards
            text_lines.append(f"{shards:>8}  {probability:8.2%}  {remaining:10.2%}")
            remaining -= probability

        # --- Banner shards table ---
        text_lines.append(f"\nBanner draws over {simulations} simulations with {pulls_limit} pulls:")
        banner_counter = Counter(banner_pulls_list)
        total_banner = sum(banner_counter.values())
        text_lines.append(f"\n{'Shards':>8}  {'Chance':>8}  {'At Least':>10}")
        text_lines.append("-" * 35)
        remaining_banner = 1.0
        for shards, count in sorted(banner_counter.items()):
            probability = count / total_banner
            text_lines.append(f"{shards:>8}  {probability:8.2%}  {remaining_banner:10.2%}")
            remaining_banner -= probability
                    
        # --- Extra Banner shards table ---
        text_lines.append(f"\nExtra banner shards over {simulations} simulations with {pulls_limit} pulls:")
        banner_counter = Counter(extra_banner_shards_list)
        total_banner = sum(banner_counter.values())
        text_lines.append(f"\n{'Shards':>8}  {'Chance':>8}  {'At Least':>10}")
        text_lines.append("-" * 35)
        remaining_banner = 1.0
        for shards, count in sorted(banner_counter.items()):
            probability = count / total_banner
            text_lines.append(f"{shards:>8}  {probability:8.2%}  {remaining_banner:10.2%}")
            remaining_banner -= probability

        result_text.append("\n".join(text_lines))

    clean()
    return result_text, all_arrays, pull_limits
def draw_heros_pie_chart(results, chart_number=-1, multiple_banner=False):
    if chart_number == -1:
        return
    if isinstance(chart_number, str):
        chart_numbers = [int(n.strip()) for n in chart_number.split(',') if n.strip().isdigit()]
    elif isinstance(chart_number, int):
        chart_numbers = [chart_number]
    else:
        return

    total_count = sum(results.values())

    # Build pools
    temp_list = Mythic_champions.copy()
    for x in banner_Mythic_champions:
        if x not in temp_list:
            temp_list.append(x)

    mythic_champs = {name: results.get(name, 0) for name in temp_list if results.get(name, 0) > 0}
    mythic_pieces = {name: results.get(name, 0) for name in Mythic_legacy if results.get(name, 0) > 0}
    legendary_champs = {name: results.get(name, 0) for name in legendary_champions if results.get(name, 0) > 0}
    legendary_pieces = {name: results.get(name, 0) for name in legendary_legacy if results.get(name, 0) > 0}
    epic_champs = {name: results.get(name, 0) for name in epic_champions if results.get(name, 0) > 0}
    epic_pieces = {name: results.get(name, 0) for name in epic_legacy if results.get(name, 0) > 0}
    banner_champion = {name: results.get(name, 0) for name in banner_Mythic_champions if results.get(name, 0) > 0}

    # Grouped data for charts 2–3
    grouped_data = [
        ("Legendary", legendary_champs | legendary_pieces),
        ("Epic", epic_champs | epic_pieces),
    ]

    # Create figure
    n = len(chart_numbers)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 6))
    if n == 1:
        axes = [axes]

    for i, idx in enumerate(chart_numbers):
        ax = axes[i]

        if idx == 1:  # Mythic grouped chart
            grouped_counts = {}

            # --- Banner handling ---
            banner_count = sum(banner_champion.values())
            if banner_count > 0:
                if multiple_banner:
                    grouped_counts["Banner"] = banner_count   # collapsed
                else:
                    # use the actual banner champion name if only one
                    if len(banner_champion) == 1:
                        champ_name = list(banner_champion.keys())[0]
                        grouped_counts[champ_name] = banner_count
                    else:
                        # safety: multiple entries, collapse them
                        grouped_counts["Banner"] = banner_count

            if multiple_banner:
                # boosted mythics go to Other
                other_champs_count = sum(
                    results.get(name, 0)
                    for name in Mythic_champions
                    if name not in banner_Mythic_champions
                )
            else:
                # boosted keep their slices
                boosted_counts = {name: results.get(name, 0) for name in boosted_Mythic_champs if results.get(name, 0) > 0}
                grouped_counts.update(boosted_counts)
                other_champs_count = sum(
                    results.get(name, 0)
                    for name in Mythic_champions
                    if name not in banner_Mythic_champions and name not in boosted_Mythic_champs
                )

            legacy_count = sum(mythic_pieces.values())

            if other_champs_count > 0:
                grouped_counts["Other Champions"] = other_champs_count
            if legacy_count > 0:
                grouped_counts["Legacy Pieces"] = legacy_count

            grouped_counts = {k: v for k, v in grouped_counts.items() if v > 0}
            labels = list(grouped_counts.keys())
            sizes = list(grouped_counts.values())

            if sizes:
                ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140, textprops={'fontsize': 8})
                ax.set_title("Mythic Breakdown (Grouped)")
            else:
                ax.set_title("Mythic Breakdown (No Data)")
                ax.axis("off")

        elif idx in {2, 3}:  # Legendary / Epic
            title, data = grouped_data[idx - 2]
            labels = list(data.keys())
            sizes = list(data.values())
            if sizes:
                ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140, textprops={'fontsize': 8})
                ax.set_title(f"{title} Breakdown")
            else:
                ax.set_title(f"{title} (No Data)")
                ax.axis("off")

        elif idx == 4:  # Overall rarity
            total_summary = {
                "Mythic - Banner": sum(banner_champion.values()),
                "Mythic - Other Champions": sum(mythic_champs.values()) - sum(banner_champion.values()),
                "Mythic - Legacy Pieces": sum(mythic_pieces.values()),
                "Legendary - Champions": sum(legendary_champs.values()),
                "Legendary - Legacy Pieces": sum(legendary_pieces.values()),
                "Epic - Champions": sum(epic_champs.values()),
                "Epic - Legacy Pieces": sum(epic_pieces.values()),
            }
            total_summary = {k: v for k, v in total_summary.items() if v > 0}

            labels = list(total_summary.keys())
            sizes = list(total_summary.values())
            total_pulls = sum(sizes)

            if sizes:
                ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140, textprops={'fontsize': 8})
                ax.set_title("Overall Rarity Composition")
            else:
                ax.set_title("Overall Rarity Composition (No Data)")
                ax.axis("off")

    plt.tight_layout()
    plt.show()
