import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.renderer.town import render_town_map

def test_visual():
    zh_cn = {
        "rooms": {
            "watch_tower": {"name": "守卫哨塔"},
            "west_gate": {"name": "西大门"},
            "range": {"name": "训练靶场"},
            "alley": {"name": "偏僻小巷"},
            "square": {"name": "中心广场"},
            "fountain": {"name": "许愿喷泉"},
            "shop": {"name": "主城商店"},
            "market": {"name": "卡牌大卖场"},
            "tavern": {"name": "酒馆大堂"},
            "vip_room": {"name": "酒馆雅间"},
            "blacksmith": {"name": "铁匠铺"}
        }
    }
    
    rooms = ["square", "alley", "market", "blacksmith", "watch_tower", "vip_room"]
    for r in rooms:
        print(f"=== {r} ===")
        print(render_town_map(r, zh_cn))
        print("=" * 60)

if __name__ == "__main__":
    test_visual()
