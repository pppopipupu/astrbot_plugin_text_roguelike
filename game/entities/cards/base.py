from ...data.card_data import CARD_CONFIG
from .neutral import (
    SpellDamageCard,
    SpellHealCard,
    GetReadyCard,
    AdrenalineCard,
    DeployAmuletCard,
    SummonMinionCard,
    AbilityCard,
    IronWillCard,
    MistyStepCard,
    ArcaneIntellectCard,
    CalculatedGambleCard,
    ManaPotionCard,
)
from .wizard import (
    MagicMissileCard,
    FireballCard,
    ThunderwaveCard,
    ShieldSpellCard,
    ArcaneSparkCard,
    EchoFormCard,
    DoomsdayJudgmentCard,
    OverchargeCard,
    MagicNetworkCard,
    FleetingSparkCard,
)
from .legendary import (
    TimeWarpCard,
    MeteorSwarmCard,
    ArchmageWishCard,
    TimeStopCard,
)
from .curse import CurseCard

ALL_CARDS = {}

for cid, cfg in CARD_CONFIG.items():
    name = cfg["name"]
    color = cfg["color"]
    ctype = cfg["type"]
    cost_a = cfg["cost_a"]
    cost_ba = cfg["cost_ba"]
    desc = cfg["desc"]
    rarity = cfg.get("rarity", "common")
    exhaust = cfg.get("exhaust", False)
    fleeting = cfg.get("fleeting", False)
    agile = cfg.get("agile", False)
    retain = cfg.get("retain", False)

    if cid == "dagger_throw":
        ALL_CARDS[cid] = SpellDamageCard(cid, name, color, ctype, cost_a, cost_ba, cfg["base_dmg"], is_fire=False, desc=desc)
    elif cid == "first_aid":
        ALL_CARDS[cid] = SpellHealCard(cid, name, color, ctype, cost_a, cost_ba, cfg["heal_amount"], desc=desc)
    elif cid == "get_ready":
        ALL_CARDS[cid] = GetReadyCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "adrenaline":
        ALL_CARDS[cid] = AdrenalineCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid in ("lucky_coin", "thorns_necklace", "ring_of_elements", "arcane_crystal", "mage_ward"):
        ALL_CARDS[cid] = DeployAmuletCard(cid, name, color, ctype, cost_a, cost_ba, cfg["countdown"], cfg["amulet_desc"], desc=desc)
    elif cid in ("mercenary", "shield_guard", "find_familiar", "arcane_golem", "water_elemental"):
        ALL_CARDS[cid] = SummonMinionCard(cid, name, color, ctype, cost_a, cost_ba, cfg["minion_hp"], cfg["minion_atk"], desc=desc)
    elif cid in ("tactical_focus", "quicken", "spell_surge", "arcane_charge"):
        ALL_CARDS[cid] = AbilityCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "iron_will":
        ALL_CARDS[cid] = IronWillCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "fire_bolt":
        ALL_CARDS[cid] = SpellDamageCard(cid, name, color, ctype, cost_a, cost_ba, cfg["base_dmg"], is_fire=True, desc=desc)
    elif cid == "magic_missile":
        ALL_CARDS[cid] = MagicMissileCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "fireball":
        ALL_CARDS[cid] = FireballCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "thunderwave":
        ALL_CARDS[cid] = ThunderwaveCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "shield":
        ALL_CARDS[cid] = ShieldSpellCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "misty_step":
        ALL_CARDS[cid] = MistyStepCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "arcane_intellect":
        ALL_CARDS[cid] = ArcaneIntellectCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "echo_form":
        ALL_CARDS[cid] = EchoFormCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "calculated_gamble":
        ALL_CARDS[cid] = CalculatedGambleCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid in ("quick_strike", "agile_strike"):
        ALL_CARDS[cid] = SpellDamageCard(cid, name, color, ctype, cost_a, cost_ba, cfg["base_dmg"], is_fire=False, desc=desc)
    elif cid == "fleeting_spark":
        ALL_CARDS[cid] = FleetingSparkCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "mana_potion":
        ALL_CARDS[cid] = ManaPotionCard(cid, name, color, ctype, cost_a, cost_ba, exhaust=exhaust, desc=desc)
    elif cid == "arcane_spark":
        ALL_CARDS[cid] = ArcaneSparkCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "overcharge":
        ALL_CARDS[cid] = OverchargeCard(cid, name, color, ctype, cost_a, cost_ba, exhaust=exhaust, desc=desc)
    elif cid == "doomsday_judgment":
        ALL_CARDS[cid] = DoomsdayJudgmentCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "time_warp":
        ALL_CARDS[cid] = TimeWarpCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "magic_network":
        ALL_CARDS[cid] = MagicNetworkCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "meteor_swarm":
        ALL_CARDS[cid] = MeteorSwarmCard(cid, name, color, ctype, cost_a, cost_ba, cfg.get("base_dmg", 0), is_fire=True, desc=desc)
    elif cid == "archmage_wish":
        ALL_CARDS[cid] = ArchmageWishCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "time_stop":
        ALL_CARDS[cid] = TimeStopCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid in ("curse_dazed", "curse_agony"):
        ALL_CARDS[cid] = CurseCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)

    ALL_CARDS[cid].rarity = rarity
    ALL_CARDS[cid].exhaust = exhaust
    ALL_CARDS[cid].fleeting = fleeting
    ALL_CARDS[cid].agile = agile
    ALL_CARDS[cid].retain = retain
    ALL_CARDS[cid].innate = cfg.get("innate", False)
    ALL_CARDS[cid].ethereal = cfg.get("ethereal", False)
    ALL_CARDS[cid].unplayable = cfg.get("unplayable", False)
