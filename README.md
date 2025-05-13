---
title: Valorant Duel Predictor
emoji: 🎮
colorFrom: red
colorTo: purple
sdk: gradio
sdk_version: 3.34.0
app_file: app.py
pinned: false
license: mit
---

## Valorant Dueling Classification Model

This model was heavily inspired by the article, "Winning Fights in VALORANT: A Predictive Analytics Approach", link [here](https://cdn.prod.website-files.com/5f1af76ed86d6771ad48324b/6228f96dd382261a4887643f_Winning%20Duels%20in%20Valorant.pdf).

I used the XGBoost (Extreme Gradient Boosting) model to predict the most likely outcome of a in-game duel based on various factors such as coordinates, loadout values and time advantage. Training/testing data used is pulled from [rib.gg](rib.gg), it comprises of data from all completed VCT tournaments, such as VCT: "Masters Tokyo". That means there actually isn't a lot of data for the model to train on quite yet and causes quite a bit of extrapolation errors (e.g. the model hasn't seen many long range operator vs classic fights as it doesn't happen often in pro play, and therefore cannot tell that the weapon difference is a bigger factor than say bomb plant status), however we can easily extend the data by feeding in other events tracked by rib.gg, such as VCL or GC. Source code for data extraction is also kept in this repo.

Example Usage:

```Python
result = predict_duel(
    models["ascent"],
    attacker_pos=(120, 200),
    defender_pos=(250, 350),
    round_time=15000,
    plant_time=None,
    attacker_weapon=Weapon.VANDAL,
    defender_weapon=Weapon.PHANTOM,
    attacker_armor_id=2,
    defender_armor_id=1
)

print(f"Prediction: {result['prediction']}")
print(f"Attacker Win Probability: {result['attacker_win_probability']:.2f}")
print(f"Defender Win Probability: {result['defender_win_probability']:.2f}")
print(result['features_used'])
# Prediction: Attacker wins
# Attacker Win Probability: 0.57
# Defender Win Probability: 0.43
# {
#     'positions': {
#         'attacker': (120, 200), 
#         'defender': (250, 350), 
#         'distance': 198.4943324127921
#     }, 
#     'timing': {
#         'round_time': 15000, 
#         'plant_time': None, 
#         'phase': 'Early', 
#         'advantage_side': 'Defender'
#     }, 
#     'weapons': {
#         'attacker_weapon_id': 4, 
#         'defender_weapon_id': 6, 
#         'advantage': 'Attacker advantage: +3'
#     }, 
#     'armor': {
#         'attacker_armor_id': 2, 
#         'defender_armor_id': 1, 
#         'advantage': 'Attacker + armor advantage'
#     }
# }

plot_positions_on_map(
    "ascent",
    attacker_pos=(120, 220),
    defender_pos=(250, 350)
)
```
![alt text](image-2.png)