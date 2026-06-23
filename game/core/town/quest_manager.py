from typing import Dict, Any, List
from ...models.state import UserStats

class QuestManager:
    @staticmethod
    def apply_strikethrough(text: str) -> str:
        return "".join(c + "\u0336" for c in text)

    @classmethod
    def render_quests(cls, stats: UserStats) -> str:
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🗺️ 【先古主城 ── 冒险者任务日志】",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        
        has_any_quest = False

        q_tour = stats.town_flags.get("quest_town_tour_state", "unstarted")
        if q_tour != "unstarted":
            has_any_quest = True
            status_text = "🎉 已完成" if q_tour == "completed" else "⏳ 进行中"
            lines.append(f"📖 任务：向导的观光指引 [{status_text}]")
            lines.append("   介绍：向导长老希望你游览主城商业区的全部11个地标以熟悉环境。")
            lines.append("   任务目标：")
            
            visited = stats.town_flags.get("quest_town_tour_visited", [])
            visited_cnt = len(visited)
            goal_text = f"探索先古主城的全部 11 个地标 (当前进度: {visited_cnt}/11)"
            if q_tour == "completed" or visited_cnt >= 11:
                lines.append("     ✔ " + cls.apply_strikethrough(goal_text))
            else:
                lines.append(f"     • {goal_text}")
            lines.append("")

        q_brew = stats.town_flags.get("quest_brew_state", "unstarted")
        if q_brew != "unstarted":
            has_any_quest = True
            status_text = "🎉 已完成" if q_brew == "completed" else "⏳ 进行中"
            lines.append(f"🍺 任务：秘密佳酿 [{status_text}]")
            lines.append("   介绍：酒保杰克急需天外甘露草来酿造传说中的秘密佳酿。")
            lines.append("   任务目标：")
            
            has_void = "void_herb" in stats.town_inventory
            has_dew = "wishing_dew" in stats.town_inventory
            is_comp = q_brew == "completed"
            
            goal1 = "获取虚空草药"
            if has_void or has_dew or is_comp:
                lines.append("     ✔ " + cls.apply_strikethrough(goal1))
            else:
                lines.append(f"     • {goal1}")
                
            goal2 = "在许愿喷泉清洗虚空草药以获得天外甘露草"
            if has_dew or is_comp:
                lines.append("     ✔ " + cls.apply_strikethrough(goal2))
            else:
                lines.append(f"     • {goal2}")
                
            goal3 = "将天外甘露草交付给酒保杰克"
            if is_comp:
                lines.append("     ✔ " + cls.apply_strikethrough(goal3))
            else:
                lines.append(f"     • {goal3}")
            lines.append("")

        q_ham = stats.town_flags.get("quest_hammer_state", "unstarted")
        if q_ham != "unstarted":
            has_any_quest = True
            status_text = "🎉 已完成" if q_ham == "completed" else "⏳ 进行中"
            lines.append(f"🔨 任务：铁锤谜案 [{status_text}]")
            lines.append("   介绍：帮铁匠艾恩克拉德找回他失窃的精钢锤，或用高仿锤子交差。")
            lines.append("   任务目标：")
            
            has_real = "smith_hammer" in stats.town_inventory
            has_fake = "fake_hammer" in stats.town_inventory
            coerced = stats.town_flags.get("noob_coerced_hammer")
            taken_bard = stats.town_flags.get("taken_smith_hammer")
            is_comp = q_ham == "completed"
            
            goal1 = "寻找关于铁锤下落的线索 (可询问巷子里的流浪诗人)"
            if has_real or has_fake or coerced or taken_bard or is_comp:
                lines.append("     ✔ " + cls.apply_strikethrough(goal1))
            else:
                lines.append(f"     • {goal1}")
                
            goal2 = "获得精钢锤或高仿铁锤"
            if has_real or has_fake or coerced or is_comp:
                lines.append("     ✔ " + cls.apply_strikethrough(goal2))
            else:
                lines.append(f"     • {goal2}")
                
            goal3 = "将铁锤带回并交给铁匠艾恩克拉德"
            if is_comp:
                lines.append("     ✔ " + cls.apply_strikethrough(goal3))
            else:
                lines.append(f"     • {goal3}")
            lines.append("")

        if not has_any_quest:
            lines.append("   📝 你当前没有任何已接取的任务。")
            lines.append("   提示：去主城各处找居民闲聊或询问他们的烦恼吧！")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("💡 提示：输入 背包/inv 查看你拥有的物品，输入 W/A/S/D 继续移动探索。")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
