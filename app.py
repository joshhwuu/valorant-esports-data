import gradio as gr
import numpy as np
import matplotlib.pyplot as plt
from enum import Enum
import xgboost as xgb
import os
from PIL import Image

class Weapon(Enum):
    KNIFE = 1
    ODIN = 2
    ARES = 3
    VANDAL = 4
    BULLDOG = 5
    PHANTOM = 6
    JUDGE = 7
    BUCKY = 8
    FRENZY = 10
    CLASSIC = 11
    GHOST = 12
    SHERIFF = 13
    SHORTY = 14
    OPERATOR = 15
    GUARDIAN = 16
    MARSHAL = 17
    SPECTRE = 18
    STINGER = 19
    OUTLAW = 23


maps = ["ascent", "bind", "haven", "icebox", "split", "breeze", "fracture", "pearl", "lotus", "sunset"]
map_images = {map_name: f"assets/{map_name}.png" for map_name in maps}

models = {}
for map_name in maps:
    if os.path.exists(f"{map_name}_model.json"):
        model = xgb.XGBClassifier()
        model.load_model(f"{map_name}_model.json")
        models[map_name] = model

def calculate_weapon_distance_advantage(attacker_weapon_id, defender_weapon_id, distance):
    """
    Calculate advantage based on weapon types at a given distance.
    Returns a numerical advantage score (positive favors attacker, negative favors defender).
    """
    knife = [1]  # Tier 0 (lowest)
    pistols = [11, 10, 12]  # Classic, Frenzy, Ghost - Tier 1
    upgraded_pistols = [13]  # Sheriff - Tier 2
    shotguns = [14, 7, 8]  # Shorty, Judge, Bucky - Tier 2
    smgs = [19, 18]  # Stinger, Spectre - Tier 3
    lmgs = [3, 2]  # Ares, Odin - Tier 4
    rifles = [5, 6, 4]  # Bulldog, Phantom, Vandal - Tier 5
    precision_rifles = [16]  # Guardian - Tier 5 
    snipers = [17, 15, 23]  # Marshal, Operator, Outlaw - Tier 6 (highest)
    
    def get_weapon_tier(weapon_id):
        weapon_id = float(weapon_id) if isinstance(weapon_id, str) else weapon_id
        
        if weapon_id in knife:
            return 0
        elif weapon_id in pistols:
            return 1
        elif weapon_id in upgraded_pistols or weapon_id in shotguns:
            return 2
        elif weapon_id in smgs:
            return 3
        elif weapon_id in lmgs:
            return 4
        elif weapon_id in rifles or weapon_id in precision_rifles:
            return 5
        elif weapon_id in snipers:
            return 6
        else:
            return 3  # Default to mid-tier for unknown weapons
        
    def get_weapon_category(weapon_id):
        weapon_id = float(weapon_id) if isinstance(weapon_id, str) else weapon_id
        
        if weapon_id in knife:
            return "knife"
        elif weapon_id in shotguns:
            return "shotgun"
        elif weapon_id in pistols or weapon_id in upgraded_pistols:
            return "pistol"
        elif weapon_id in smgs:
            return "smg"
        elif weapon_id in lmgs:
            return "lmg"
        elif weapon_id in rifles:
            return "rifle"
        elif weapon_id in precision_rifles:
            return "precision_rifle"
        elif weapon_id in snipers:
            return "sniper"
        else:
            return "unknown"
    
    attacker_category = get_weapon_category(attacker_weapon_id)
    defender_category = get_weapon_category(defender_weapon_id)
    
    attacker_tier = get_weapon_tier(attacker_weapon_id)
    defender_tier = get_weapon_tier(defender_weapon_id)
    tier_advantage = (attacker_tier - defender_tier) * 2
    
    if attacker_category == "knife" and defender_category != "knife":
        return -10
    elif defender_category == "knife" and attacker_category != "knife":
        return 10
    elif attacker_category == defender_category:
        return 0
    
    situational_advantage = 0
    
    # Short range (5-15m) - shotguns and SMGs shine
    if distance < 50:
        if attacker_category == "shotgun":
            situational_advantage += 5  # Shotguns deadly at point blank
        
        if defender_category == "sniper":
            situational_advantage += 4  # Snipers terrible in close quarters
        elif defender_category == "rifle" or defender_category == "precision_rifle":
            situational_advantage += 1  # Rifles at slight disadvantage up close
    
    # Short range (5-15m) - shotguns and SMGs shine
    elif distance < 150:  
        if attacker_category == "shotgun":
            situational_advantage += 1
        elif attacker_category == "smg":
            situational_advantage += 2
        elif attacker_category == "knife":
            situational_advantage -= 6  # Knife bad beyond point blank
            
        if defender_category == "sniper":
            situational_advantage += 3  # Snipers still bad at short range
    
    # Mid range (15-30m) - rifles optimal
    elif distance < 300:  
        if attacker_category in ["rifle", "lmg", "precision_rifle"]:
            situational_advantage += 3
        elif attacker_category == "shotgun":
            situational_advantage -= 3  # Shotguns poor at mid range
        elif attacker_category == "knife":
            situational_advantage -= 10  # Knife impossible at mid range
            
        if defender_category in ["pistol", "shotgun"]:
            situational_advantage += 2
    
    # Long range (30m+) - snipers dominate
    else:  
        if attacker_category == "sniper":
            situational_advantage += 5
        elif attacker_category == "precision_rifle":
            situational_advantage += 2
        elif attacker_category in ["pistol", "smg", "shotgun", "knife"]:
            situational_advantage -= 4  # Short range weapons terrible at long range
            
        if defender_category == "sniper":
            situational_advantage -= 5
        elif defender_category == "precision_rifle":
            situational_advantage -= 2
    
    if attacker_category == "knife" and defender_category != "knife":
        situational_advantage -= 6  # Severe disadvantage for knife vs gun
        
    if defender_category == "knife" and attacker_category != "knife":
        situational_advantage += 6  # Severe advantage against knife
    
    total_advantage = tier_advantage + situational_advantage
    
    return max(min(total_advantage, 10), -10)

def predict_duel(model, attacker_pos, defender_pos, 
                round_time, plant_time=None,
                attacker_weapon=None, defender_weapon=None,
                attacker_armor_id=0, defender_armor_id=0):
    """
    Predict the winner of an engagement between an attacker and defender.
    
    Parameters:
    -----------
    model : XGBoost model
        The trained model for the specific map
    attacker_pos : tuple (x, y)
        Position coordinates of the attacking player
    defender_pos : tuple (x, y)
        Position coordinates of the defending player
    round_time : int
        Time in milliseconds since round start
    plant_time : int or None
        Time in milliseconds when bomb was planted (None if not planted)
    attacker_weapon : Weapon enum or int
        Weapon used by attacker (either Weapon enum or weapon ID)
    defender_weapon : Weapon enum or int
        Weapon used by defender (either Weapon enum or weapon ID)
    attacker_armor_id : int
        Armor ID of attacking player (default 0)
    defender_armor_id : int
        Armor ID of defending player (default 0)
        
    Returns:
    --------
    dict
        Contains prediction outcome and probabilities
    """
    
    attacker_weapon_id = attacker_weapon.value if isinstance(attacker_weapon, Weapon) else attacker_weapon
    defender_weapon_id = defender_weapon.value if isinstance(defender_weapon, Weapon) else defender_weapon
    
    distance = np.sqrt((attacker_pos[0] - defender_pos[0])**2 + 
                       (attacker_pos[1] - defender_pos[1])**2)
    
    early_round_time = 20000  # 20 seconds
    is_early_round = (round_time < early_round_time)
    is_post_plant = (plant_time is not None and round_time > plant_time)
    
    if is_post_plant:
        time_advantage = -1  # Attacker advantage (negative value)
    elif is_early_round:
        time_advantage = 1   # Defender advantage (positive value)
    else:
        time_advantage = 0   # Neutral
    
    weapon_advantage = 0
    weapon_advantage_description = "No weapon data provided"
    
    if attacker_weapon_id is not None and defender_weapon_id is not None:
        weapon_advantage = calculate_weapon_distance_advantage(
            attacker_weapon_id, defender_weapon_id, distance
        )
        
        if weapon_advantage > 0:
            weapon_advantage_description = f"Attacker advantage: +{weapon_advantage}"
        elif weapon_advantage < 0:
            weapon_advantage_description = f"Defender advantage: +{abs(weapon_advantage)}"
        else:
            weapon_advantage_description = "No weapon advantage"
    
    armor_advantage = attacker_armor_id - defender_armor_id
    
    features = np.array([[
        attacker_pos[0], attacker_pos[1],    # killer_x, killer_y
        defender_pos[0], defender_pos[1],    # victim_x, victim_y
        distance,                            # distance
        weapon_advantage,                    # weapon_distance_advantage
        armor_advantage,                     # armor_advantage
        time_advantage                       # time_advantage
    ]])
    
    attacker_win_probability = float(model.predict_proba(features)[0, 1])
    
    return {
        "prediction": "Attacker wins" if attacker_win_probability > 0.5 else "Defender wins",
        "attacker_win_probability": attacker_win_probability,
        "defender_win_probability": 1 - attacker_win_probability,
        "features_used": {
            'positions': {
                "attacker": attacker_pos, 
                "defender": defender_pos,
                "distance": distance
            },
            "timing": {
                "round_time": round_time,
                "plant_time": plant_time,
                "phase": "Post-plant" if is_post_plant else ("Early" if is_early_round else "Mid"),
                "advantage_side": "Attacker" if time_advantage < 0 else ("Defender" if time_advantage > 0 else "Neutral")
            },
            "weapons": {
                "attacker_weapon_id": attacker_weapon_id,
                "defender_weapon_id": defender_weapon_id,
                "advantage": weapon_advantage_description
            },
            "armor": {
                "attacker_armor_id": attacker_armor_id,
                "defender_armor_id": defender_armor_id,
                "advantage": f"{'Attacker +' if armor_advantage > 0 else 'Defender +' if armor_advantage < 0 else 'No'} armor advantage"
            }
        }
    }

def select_positions(map_name, evt: gr.SelectData):
    global attacker_pos, defender_pos, current_selection
    
    if current_selection == "attacker":
        attacker_pos = (evt.index[0], evt.index[1])
        current_selection = "defender"
        return f"Attacker position: {attacker_pos}", "Now select defender position..."
    else:
        defender_pos = (evt.index[0], evt.index[1])
        current_selection = "attacker" 
        return f"Attacker: {attacker_pos}, Defender: {defender_pos}", "Positions set"

def plot_positions_on_map(map_name, attacker_pos, defender_pos):
    image_path = f"assets/{map_name}.png"
    
    if not os.path.exists(image_path):
        print(f"Warning: Map image not found at {image_path}")
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.set_xlim(1024, 0)
        ax.set_ylim(1024, 0)
        ax.grid(True)
    else:
        map_img = plt.imread(image_path)
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.imshow(map_img, extent=[0, 1024, 1024, 0])
    
    ax.plot(attacker_pos[0], attacker_pos[1], "r^", markersize=15, label="Attacker")
    
    ax.plot(defender_pos[0], defender_pos[1], "bo", markersize=12, label="Defender")
    
    ax.plot([attacker_pos[0], defender_pos[0]], [attacker_pos[1], defender_pos[1]], 
            "k--", alpha=0.6)
    distance = np.sqrt((attacker_pos[0] - defender_pos[0])**2 + 
                       (attacker_pos[1] - defender_pos[1])**2)
    ax.text((attacker_pos[0] + defender_pos[0])/2, 
            (attacker_pos[1] + defender_pos[1])/2 - 20,
            f"Distance: {distance:.1f} units", 
            color="white", fontsize=12,
            bbox=dict(facecolor="black", alpha=0.7))
    
    ax.set_title(f"Engagement Position on {map_name.capitalize()}")
    ax.legend(loc="upper right")
    
    return fig, ax

def make_prediction(map_name, round_time, plant_time_enabled, plant_time,
                   attacker_weapon, defender_weapon, attacker_armor, defender_armor):
    
    if not plant_time_enabled:
        plant_time = None
        
    # Convert weapon names to enum
    attacker_weapon_enum = Weapon[attacker_weapon]
    defender_weapon_enum = Weapon[defender_weapon]
    
    # Make prediction
    result = predict_duel(
        models[map_name],
        attacker_pos=attacker_pos,
        defender_pos=defender_pos,
        round_time=round_time * 1000,  # Convert to milliseconds
        plant_time=None if plant_time is None else plant_time * 1000,
        attacker_weapon=attacker_weapon_enum,
        defender_weapon=defender_weapon_enum,
        attacker_armor_id=int(attacker_armor),
        defender_armor_id=int(defender_armor)
    )
    
    # Create visualization
    fig = plot_positions_on_map(map_name, attacker_pos, defender_pos)
    
    # Format results
    result_text = f"""
    ## Prediction: {result['prediction']}
    - Attacker Win Probability: {result['attacker_win_probability']:.2f}
    - Defender Win Probability: {result['defender_win_probability']:.2f}
    
    ### Details:
    - Distance: {result['features_used']['positions']['distance']:.1f} units
    - Phase: {result['features_used']['timing']['phase']}
    - Weapon advantage: {result['features_used']['weapons']['advantage']}
    - Armor: {result['features_used']['armor']['advantage']}
    """
    
    return fig, result_text

attacker_pos = (0, 0)
defender_pos = (0, 0)
current_selection = "attacker"

with gr.Blocks() as demo:
    gr.Markdown("# Valorant Duel Classifier")
    gr.Markdown("Select positions, weapons, and other parameters to predict duel outcomes")
    
    with gr.Row():
        with gr.Column(scale=2):
            map_dropdown = gr.Dropdown(choices=maps, value="ascent", label="Select Map")
            map_image = gr.Image(map_images["ascent"], label="Click to select positions")
            position_display = gr.Textbox(value="No positions selected", label="Selected Positions")
            selection_status = gr.Textbox(value="Select attacker position first", label="Status")

            map_image.select(select_positions, inputs=[map_dropdown], outputs=[position_display, selection_status])

            map_dropdown.change(lambda map_name: map_images[map_name], inputs=[map_dropdown], outputs=[map_image])
        
        with gr.Column(scale=1):
            with gr.Group():
                gr.Markdown("## Timing")
                round_time = gr.Slider(0, 100, value=15, label="Round Time (seconds)")
                plant_enabled = gr.Checkbox(label="Bomb Planted?", value=False)
                plant_time = gr.Slider(0, 100, value=0, label="Plant Time (seconds)", visible=False)
                plant_enabled.change(lambda x: gr.update(visible=x), inputs=[plant_enabled], outputs=[plant_time])
            
            with gr.Group():
                gr.Markdown("## Attacker")
                attacker_weapon = gr.Dropdown(
                    choices=[w.name for w in Weapon], 
                    value="VANDAL", 
                    label="Attacker Weapon"
                )
                attacker_armor = gr.Radio(choices=["0", "1", "2"], value="2", label="Attacker Armor (0=None, 1=Light, 2=Heavy)")
                
            with gr.Group():
                gr.Markdown("## Defender")
                defender_weapon = gr.Dropdown(
                    choices=[w.name for w in Weapon], 
                    value="PHANTOM", 
                    label="Defender Weapon"
                )
                defender_armor = gr.Radio(choices=["0", "1", "2"], value="2", label="Defender Armor (0=None, 1=Light, 2=Heavy)")
            
            predict_button = gr.Button("Predict Outcome")
    
    with gr.Row():
        with gr.Column():
            output_plot = gr.Plot(label="Duel Visualization")
        with gr.Column():
            output_result = gr.Markdown(label="Prediction Results")
    
    predict_button.click(
        make_prediction,
        inputs=[map_dropdown, round_time, plant_enabled, plant_time, 
                attacker_weapon, defender_weapon, attacker_armor, defender_armor],
        outputs=[output_plot, output_result]
    )

demo.launch()
