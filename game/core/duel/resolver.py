from typing import Optional

class DuelResolver:
    def __init__(self, engine):
        self.engine = engine

    def use_coin(self, run, user_id: str) -> str:
        current_turn_id = run.node_data.get("current_turn_id")
        if user_id != current_turn_id:
            return "❌ 现在不是你的回合，无法使用幸运币。"
        p1_id = run.node_data["player1_id"]
        prefix = "p1" if user_id == p1_id else "p2"
        coins = run.node_data.get(f"{prefix}_coins", 0)
        if coins <= 0:
            return "❌ 你没有幸运币了。"
        run.node_data[f"{prefix}_coins"] = coins - 1
        run.player.actions += 1
        self.engine._log_event(run, "🪙 玩家使用了幸运币，获得了 1 点动作点 (A)。")
        return "✅ 使用幸运币成功，动作点增加 1A。"

    def evolve_card(self, run, user_id: str, target: str) -> str:
        current_turn_id = run.node_data.get("current_turn_id")
        if user_id != current_turn_id:
            return "❌ 现在不是你的回合，无法进化卡牌。"
        tc = run.node_data.get("turn_count", 1)
        if tc < 3:
            return "❌ 进化点第 3 回合起才可使用（当前第 {} 回合）。".format(tc)
        p1_id = run.node_data["player1_id"]
        prefix = "p1" if user_id == p1_id else "p2"
        if run.node_data.get(f"{prefix}_evolved_this_turn", False):
            return "❌ 每回合只能进化一张牌。"
        ev = run.node_data.get(f"{prefix}_evolve_points", 4)
        if ev <= 0:
            return "❌ 你的进化点已用完。"
        p = run.player
        if target.isdigit():
            idx = int(target) - 1
            if 0 <= idx < len(p.hand):
                from ...models.state import ensure_card_state
                cid = ensure_card_state(p.hand[idx])
                p.hand[idx] = cid
                if cid.upgraded:
                    return "❌ 该卡牌已经是强化版本了。"
                import copy
                new_cid = copy.copy(cid)
                new_cid.upgraded = True
                p.hand[idx] = new_cid
                run.node_data[f"{prefix}_evolved_this_turn"] = True
                run.node_data[f"{prefix}_evolve_points"] = ev - 1
                self.engine._log_event(run, "✨ 进化了手牌中的卡牌为强化版！")
                return f"✨ 成功将手牌 [{idx+1}] 进化为强化版。"
            else:
                return "❌ 序号超出范围。"
        if target.startswith("p") and len(target) > 1:
            grid = target[1:]
            if grid in p.minions:
                m = p.minions[grid]
                if m.name.endswith("+"):
                    return "❌ 该随从已经是进化形态。"
                m.max_hp += 2
                m.hp = m.max_hp
                m.atk += 2
                m.name += "+"
                run.node_data[f"{prefix}_evolved_this_turn"] = True
                run.node_data[f"{prefix}_evolve_points"] = ev - 1
                self.engine._log_event(run, f"✨ 进化了随从 【{m.name[:-1]}】！")
                return f"✨ 成功将随从 【{m.name[:-1]}】 进化为强化形态 【{m.name}】（生命补满并上限+2，攻击力+2）。"
            elif grid in p.amulets:
                a = p.amulets[grid]
                if a.name.endswith("+"):
                    return "❌ 该护符已经是强化形态。"
                a.name += "+"
                run.node_data[f"{prefix}_evolved_this_turn"] = True
                run.node_data[f"{prefix}_evolve_points"] = ev - 1
                self.engine._log_event(run, f"✨ 进化了护符 【{a.name[:-1]}】！")
                return f"✨ 成功将护符 【{a.name[:-1]}】 进化为 【{a.name}】。"
            else:
                return "❌ 我方格子中不存在可进化的实体。"
        return "❌ 进化的目标不合法（请提供手牌序号或我方格子，如 1 或 p1）。"

    def minion_attack(self, run, my_grid: str, opp_grid: Optional[str] = None) -> str:
        p = run.player
        if my_grid not in p.minions:
            return f"❌ 我方格子 [{my_grid}] 没有随随从。"
        m = p.minions[my_grid]
        if m.attack_actions < 1:
            return "❌ 该随从本回合已经没有可用的攻击动作（AA）点。"
        has_rush = any(b.id == "rush_buff" for b in m.buffs)
        if opp_grid is None:
            for i in range(1, 7):
                if str(i) in run.player2.minions:
                    opp_grid = f"e{i+1}"
                    break
            if not opp_grid:
                opp_grid = "e1"
        if opp_grid == "e1" and has_rush:
            return f"❌ 随从【{m.name}】本回合处于突进状态，只能攻击敌方随从，无法直接攻击领主。"
        m.attack_actions -= 1
        m.actions -= 1
        target_name = "未知"
        if opp_grid == "e1":
            p1_id = run.node_data["player1_id"]
            target_name = run.node_data.get("player2_name" if run.user_id == p1_id else "player1_name", "对手")
            self.engine._damage_target(run, "e1", m.atk, source=f"p{my_grid}", damage_type="attack")
            res = f"我方随从【{m.name}】攻击了敌方领主【{target_name}】。"
        elif opp_grid.startswith("e") and len(opp_grid) > 1:
            try:
                opp_idx = int(opp_grid[1:]) - 1
            except ValueError:
                opp_idx = 0
            opp_grid_clean = str(opp_idx)
            p2 = run.player2
            if opp_grid_clean not in p2.minions:
                return f"❌ 敌方战场对应格子 [{opp_grid_clean}] 没有随从存在。"
            enemy_m = p2.minions[opp_grid_clean]
            target_name = enemy_m.name
            res = f"我方随从【{m.name}】攻击了敌方随从【{target_name}】。"
            self.engine._damage_target(run, opp_grid, m.atk, source=f"p{my_grid}", damage_type="attack")
            if opp_grid_clean in p2.minions:
                self.engine._damage_target(run, f"p{my_grid}", enemy_m.atk, source=opp_grid, damage_type="attack")
        else:
            return "❌ 攻击目标非法，随从只能攻击 e1-e7。"
        return res

    def minion_skill(self, run, my_grid: str, skill_idx: int = 1, target: Optional[str] = None) -> str:
        p = run.player
        if my_grid not in p.minions:
            return f"❌ 我方格子 [{my_grid}] 没有随从。"
        m = p.minions[my_grid]
        try:
            from ...entities.minions.minions import ALL_MINIONS
        except ImportError:
            try:
                from ...entities.minions.minions import ALL_MINIONS
            except ImportError:
                from ...entities.minions import ALL_MINIONS
        if m.id not in ALL_MINIONS:
            return f"❌ 随从【{m.name}】没有任何可用技能。"
        template = ALL_MINIONS[m.id]
        skills_list = template.skills
        if skill_idx < 1 or skill_idx > len(skills_list):
            skills_desc = "\n".join([f" [{idx}] {s.name}: {s.desc}" for idx, s in enumerate(skills_list, 1)])
            return f"❌ 无效的技能序号。随从【{m.name}】的可用技能有：\n{skills_desc}"
        skill = skills_list[skill_idx - 1]
        cost_a = skill.cost_a
        cost_ba = skill.cost_ba
        if m.actions < cost_a or m.bonus_actions < cost_ba:
            return f"❌ 随从资源不足（需要 {cost_a}A {cost_ba}BA，当前 {m.actions}A {m.bonus_actions}BA）。"
        needs_target = False
        base_id = m.id.rstrip("+")
        if base_id == "mercenary" and skill_idx == 1:
            needs_target = True
        elif base_id == "shield_guard" and skill_idx == 2:
            needs_target = True
        elif base_id == "water_elemental" and skill_idx == 2:
            needs_target = True
        if needs_target:
            if target is None:
                for i in range(1, 7):
                    if str(i) in run.player2.minions:
                        target = f"e{i+1}"
                        break
                if not target:
                    target = "e1"
            if isinstance(target, str) and target.isdigit():
                target = f"e{target}"
            if target == "0" or target == "e0":
                target = "e1"
            if target.startswith("e"):
                if target == "e1":
                    pass
                else:
                    try:
                        opp_grid = str(int(target[1:]) - 1)
                    except ValueError:
                        opp_grid = "0"
                    if opp_grid not in run.player2.minions:
                        return f"❌ 敌方目标 [{target}] 不存在。"
            else:
                return "❌ 无效的目标。该技能只能对敌方目标释放。"
        m.actions -= cost_a
        m.bonus_actions -= cost_ba
        msg = f"随从【{m.name}】发动了技能【{skill.name}】！"
        effect_msg = skill.execute(run, my_grid, target, self.engine)
        msg += effect_msg
        return msg
