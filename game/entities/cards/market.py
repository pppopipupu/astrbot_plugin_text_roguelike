MARKET_CARDS = {
    "warrior_blood_fury",
    "neutral_power_word_pain",
    "warrior_shield_bash",
    "wizard_antimagic_field",
    "neutral_power_word_stun",
    "warrior_hell_raider",
    "wizard_prismatic_wall",
    "wizard_time_ravage",
    "neutral_power_word_kill",
    "neutral_plane_shift"
}

def is_card_available(cid: str, stats) -> bool:
    if not cid:
        return False
    clean_cid = cid.split(":replay:")[0].split(":fragile:")[0]
    if clean_cid.endswith("+"):
        clean_cid = clean_cid[:-1]
    if clean_cid in MARKET_CARDS:
        if not stats:
            return False
        unlocked = set(getattr(stats, "unlocked_new_cards", []) or []) | set(getattr(stats, "purchased_pool", []) or [])
        return clean_cid in unlocked
    return True
