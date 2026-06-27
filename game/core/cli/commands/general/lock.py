from typing import Generator
from ...base import CommandHandler
from .....renderer import GameRenderer
from .....entities import ALL_CARDS

class LockCommand(CommandHandler, names=["锁定", "lock", "锁定管理", "解锁", "unlock"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        stats = router.save_manager.load_stats(user_id)
        if not hasattr(stats, "locked_cards") or stats.locked_cards is None:
            stats.locked_cards = []
        locked_list = stats.locked_cards
        cmd = parts[0].lower()

        rarity_map = {
            "common": "普通",
            "rare": "稀有",
            "epic": "珍奇",
            "legendary": "传奇",
            "mythic": "神话",
            "artifact": "神器",
            "curse": "诅咒"
        }

        if len(parts) == 1:
            if cmd in ("解锁", "unlock"):
                yield "❌ 指令错误：请指定要解锁的卡牌名称，例如：/rogue unlock 痛击"
                return

            gp = getattr(stats, "gp", 0)
            lines = [
                "━━━━━━━━━━━━━━━━━━━━",
                "🔒 魔法肉鸽卡牌 ── 锁定卡牌管理系统",
                "━━━━━━━━━━━━━━━━━━━━",
                f"💰 我的 GP 资产：{gp} GP",
                f"📌 当前锁定卡牌 ({len(locked_list)} / 8)：",
            ]
            if locked_list:
                for idx, cid in enumerate(locked_list):
                    c_obj = ALL_CARDS.get(cid)
                    cname = c_obj.name if c_obj else cid
                    crarity_ch = rarity_map.get(getattr(c_obj, "rarity", "common"), "普通")
                    lines.append(f"  {idx+1}. 【{cname}】 ({crarity_ch})")
            else:
                lines.append("  • 暂无任何锁定的卡牌。")

            lines.extend([
                "",
                "【锁定规则说明】",
                "1. 允许多局/多次游戏持续生效，无需每局重复付费锁定！",
                "2. 最多可同时锁定 8 张卡牌。开局卡组不足部分将随机补充。",
                "3. 仅限锁定普通、稀有、珍奇卡牌（不可锁定传奇及以上稀有度）。",
                "4. 锁定卡牌在管理界面中进行添加（每次新锁卡需支付 300 GP 费用）。",
                "5. 解锁（移除已锁卡牌）完全免费，退还的名额可供重新选锁其他卡牌。",
                "",
                "【锁定管理快捷指令】",
                "👉 /rogue lock <卡牌中文名> ── 锁定一张必带卡（消耗 300 GP）",
                "👉 /rogue unlock <卡牌中文名> ── 解锁并移除该必带卡（免费）",
                "👉 /rogue lock clear ── 清空所有锁定的必带卡（免费）",
                "━━━━━━━━━━━━━━━━━━━━"
            ])
            yield "\n".join(lines)
            return

        arg1 = parts[1].strip()
        if arg1.lower() in ("clear", "清空", "重置", "reset") and cmd in ("锁定", "lock", "锁定管理"):
            stats.locked_cards.clear()
            router.save_manager.save_stats(user_id, stats)
            yield "🔑 已成功清空所有开局锁定必带的卡牌！"
            return

        is_unlock = (cmd in ("解锁", "unlock")) or (arg1.lower() in ("unlock", "解锁", "remove", "移除"))
        if is_unlock:
            card_name = parts[2].strip() if arg1.lower() in ("unlock", "解锁", "remove", "移除") and len(parts) >= 3 else arg1
            target_cid = None
            for cid, c_obj in ALL_CARDS.items():
                if c_obj.name == card_name or cid.lower() == card_name.lower():
                    target_cid = cid
                    break
            
            if not target_cid and card_name.endswith("+"):
                base_name = card_name[:-1]
                for cid, c_obj in ALL_CARDS.items():
                    if c_obj.name == base_name or cid.lower() == base_name.lower():
                        target_cid = cid
                        break

            if not target_cid:
                target_cid = card_name

            if target_cid in stats.locked_cards:
                stats.locked_cards.remove(target_cid)
                router.save_manager.save_stats(user_id, stats)
                c_obj = ALL_CARDS.get(target_cid)
                cname = c_obj.name if c_obj else target_cid
                yield f"🔓 解锁成功：已将卡牌【{cname}】从你的开局必带锁定列表中移除。"
            else:
                yield f"❌ 移除失败：你的锁定列表中没有卡牌【{card_name}】。"
            return

        card_name = arg1
        target_cid = None
        for cid, c_obj in ALL_CARDS.items():
            if c_obj.name == card_name or cid.lower() == card_name.lower():
                target_cid = cid
                break

        if not target_cid:
            yield f"❌ 未找到名为【{card_name}】的卡牌信息。"
            return

        if target_cid.endswith("+"):
            target_cid = target_cid[:-1]

        c_obj = ALL_CARDS[target_cid]
        r = getattr(c_obj, "rarity", "common")
        if r in ("legendary", "mythic", "artifact", "curse"):
            yield f"❌ 锁定失败：无法锁定【{rarity_map.get(r, r)}】稀有度的卡牌。"
            return

        if target_cid in stats.locked_cards:
            yield f"❌ 锁定失败：卡牌【{c_obj.name}】已经在你的锁定列表中了。"
            return

        if len(stats.locked_cards) >= 8:
            yield "❌ 锁定失败：最多只能同时锁定 8 张卡牌。"
            return

        if stats.gp < 300:
            yield f"❌ 锁定失败：锁定卡牌需要 300 GP，当前仅有 {stats.gp} GP。"
            return

        stats.gp -= 300
        stats.locked_cards.append(target_cid)
        router.save_manager.save_stats(user_id, stats)
        yield f"🔑 锁定成功：已扣除 300 GP，卡牌【{c_obj.name}】已加入你的开局必带锁定列表中！"
