DUEL_BROADCAST_TEMPLATES = {
    "play_not_my_turn": "❌ 当前是对方的回合，请耐心等待。",
    "play_no_idx": "❌ 请输入要使用的手牌序号，例如：/rogue p 1",
    "play_invalid_idx": "❌ 请提供合法的数字序号。",
    "play_out_of_range": "❌ 手牌序号超出范围。",
    "play_no_card_entity": "❌ 未找到对应卡牌实体。",
    "play_insufficient_actions": "❌ 动作点不足，该牌需要 {cost_a}A {cost_ba}BA，你当前有 {actions}A {bonus_actions}BA。",
    "play_minion_only": "❌ 该卡牌只能以随人为目标，无法以敌方领主为目标。",
    "play_minion_only_err": "❌ 该卡牌只能以随从为目标，无法以敌方领主为目标。",
    "time_stop_damage_interrupted": "⏳ [时间停止] 额外回合中对敌方造成了伤害，当前额外回合提前结束！",
    "play_card_tip": "📢 玩家【{sender_name}】打出了卡牌【{card_name}】！",
    "minion_no_idx": "❌ 请输入我方随从格子序号，例如：/rogue m 1 a e1",
    "minion_not_found": "❌ 找不到我方随从格子 [{grid}]。",
    "minion_stunned": "❌ 随从【{name}】处于眩晕状态，无法行动。",
    "minion_attack_tip": "📢 玩家【{sender_name}】指挥随从【{minion_name}】攻击了【{target_name}】！",
    "coin_success_tip": "📢 玩家【{sender_name}】使用了幸运币，获得了 1 点动作点！",
    "evolve_no_target": "❌ 请输入进化目标手牌序号或格子，例如：/rogue ev 1 或 /rogue ev p1",
    "evolve_tip": "📢 玩家【{sender_name}】将{evolve_target_name}进化了！",
    "end_turn_not_my_turn": "❌ 现在不是你的回合，无法结束回合。",
    "end_turn_tip": "📢 玩家【{sender_name}】结束了回合！",
    "accept_no_invite": "❌ 你当前没有收到 any 未处理的对决邀请。",
    "accept_sender_deck_invalid": "❌ 无法开始：发起方牌组不合法（{err}）。",
    "accept_receiver_deck_invalid": "❌ 无法开始：你的活动牌组不合法（{err}）。请进行构筑并保证 25~50 张牌。",
    "abandon_not_in_game": "❌ 你当前不在任何对局中。",
    "abandon_no_save": "❌ 未找到对应对战存档。",
    "abandon_win_announcement": "🏳️ 玩家【{my_name}】直接认输了！对决结束，玩家【{opp_name}】获得了最终胜利！获得 2000 GP！",
    "abandon_self_tip": "🏳️ 你已认输，本局对战结束。",
    "mode_toggle_tip": "✨ 免前缀对决模式已{status_str}！此设置仅对你个人生效。",
    "invite_no_target": "❌ 请指定要邀请的对方用户 ID，例如：/rogue duel invite @玩家",
    "invite_no_match": "❌ 未匹配到被邀请的对方用户 ID。",
    "invite_self": "❌ 不能与自己进行对决。",
    "invite_deck_invalid": "❌ 无法发起邀请：你的活动牌组不合法（{err}）。请先进行构筑并保证 25~50 张牌。",
    "invite_public_tip": "⚔️ 玩家【{sender_name}】向你发起了 TCG 卡牌对决！请输入 /rogue duel accept 以开始对战！",
    "invite_private_tip": "⚔️ 【{sender_name}】向你发起了 TCG 卡牌对决！输入 /rogue duel accept 开始对局！",
    "deck_list_title": "📋 【你的对决牌组列表】",
    "deck_list_empty": "（无任何牌组，请输入 /rogue duel deck create <名称> 进行创建）",
    "deck_list_item": " [{idx}] {name} ({len_cards}张卡) | {valid_tag} {act_tag}",
    "deck_create_no_name": "❌ 请输入牌组名称，例如：/rogue duel deck create 我的卡组1",
    "deck_create_empty_name": "❌ 牌组名称不能为空。",
    "deck_create_exists": "❌ 牌组【{name}】已存在。",
    "deck_create_success": "✅ 成功创建空牌组【{name}】，已自动设为当前选中牌组。",
    "deck_select_no_target": "❌ 请指定要选择的牌组序号或名称。",
    "deck_select_out_of_range": "❌ 序号超出范围。",
    "deck_select_not_found": "❌ 牌组【{name}】不存在。",
    "deck_select_success": "✅ 已成功切换当前活动牌组为【{name}】。",
    "deck_info_not_found": "❌ 未找到指定牌组或当前没有选中的活动牌组。",
    "deck_info_title": "📋 牌组【{name}】详情 ({len_cards}张 | {status_str})",
    "deck_info_empty": "（空空如也，请输入 /rogue duel deck add <卡牌> 填充它）",
    "deck_info_item": " [{idx}] {card_name} (消耗: {cost_str}) x {count}",
    "deck_add_no_active": "❌ 当前没有选中的活动牌组，请先创建或选择一个牌组。",
    "deck_add_no_card": "❌ 请输入卡牌名称或拼音，例如：/rogue duel deck add 挥砍 4",
    "deck_add_not_found": "❌ 未找到符合条件的对决卡牌。",
    "deck_add_multiple_matches": "❌ 匹配到多个结果：{matches}，请提供更精确的名称。",
    "deck_add_full": "❌ 牌组容量已满，不可超过 50 张。",
    "deck_add_mythic_limit": "❌ 单卡超限：神话或神器卡【{cname}】在每个牌组中限制只能携带 1 张（当前已有 {cur_count} 张）。",
    "deck_add_legendary_limit": "❌ 单卡超限：传奇卡【{cname}】在每个牌组中限制只能携带 2 张（当前已有 {cur_count} 张）。",
    "deck_add_common_limit": "❌ 单卡超限：【{cname}】在牌组里已有 {cur_count} 张，同名基础卡上限为 4 张。",
    "deck_add_success": "✅ 成功往牌组【{active}】添加了 {count} 张 【{cname}】。",
    "deck_remove_no_active": "❌ 当前没有选中的活动牌组。",
    "deck_remove_no_idx": "❌ 请指定卡牌详情中的序号，例如：/rogue duel deck remove 2",
    "deck_remove_invalid_idx": "❌ 必须输入详情中的序号进行移除。",
    "deck_remove_out_of_range": "❌ 序号超出范围。",
    "deck_remove_success": "✅ 成功从牌组【{active}】移除了 {actual_rem} 张 【{cname}】。",
    "deck_export_no_deck": "❌ 未找到指定牌组或当前没有选中的活动牌组。",
    "deck_export_success": "✨ 牌组【{name}】导出成功！分享码如下（长按复制）：\n{code}\n\n可以使用以下指令导入：\n/rogue duel deck import <分享码> [新牌组名称]",
    "deck_export_failed": "❌ 导出分享码失败: {err}",
    "deck_import_no_code": "❌ 请提供牌组分享码，例如：/rogue duel deck import <分享码> [自定义名称]",
    "deck_import_decode_failed": "❌ 解析分享码失败，请检查分享码是否完整或正确: {err}",
    "deck_import_invalid_format": "❌ 分享码格式不正确：解析后的数据结构无效。",
    "deck_import_invalid_cards": "❌ 分享码卡牌列表数据格式错误。",
    "deck_import_invalid_card_type": "❌ 分享码中包含非法的卡牌ID类型: {ctype}",
    "deck_import_unknown_card": "❌ 分享码中包含未知的对决卡牌ID: {cid}，导入中止。",
    "deck_import_success": "✅ 成功导入牌组【{final_name}】（共 {len_cards} 张卡）并设为当前活动牌组。\n卡组状态：{status_msg}",
    "deck_invalid_count": "卡牌数量不合法（当前 {len_cards} 张，应在 25~50 张之间）。",
    "deck_invalid_mythic_limit": "单卡超限：神话或神器卡【{name}】在每个牌组中限制只能携带 1 张。",
    "deck_invalid_legendary_limit": "单卡超限：传奇卡【{name}】在每个牌组中限制只能携带 2 张。",
    "deck_invalid_common_limit": "单卡超限：【{name}】超过了 4 张限制。",
    "query_no_query": "❌ 请输入具体的查询内容。",
    "query_not_in_battle": "❌ 只有在对战中才能查询详细战斗信息。请输入想要查询的卡牌、随从、Buff名称。\n💡 提示：你可以输入：对决查询 <名称>（如：对决查询 痛击）或对决查询 buff 查看相关介绍。",
    "query_not_in_battle_pile": "❌ 只有在对决战斗中才能查询对决{sub_query}。",
    "query_pile_sent_private": "✨ 对局当前【{sub_query}】信息已通过私聊发送给你！",
    "query_unknown": "❌ 未知的查询指令。",
    "query_no_match": "❌ 未在对决模式中匹配到“{query_str}”相关的卡牌、随从、Buff、遗物或词条信息。",
    "query_title": "🔍 对决查询结果：{query_str}",
    "query_card_header": "🎴 对决卡牌：【{name}】 ({rname})",
    "query_card_detail": "类型：{ctype} | 消耗: {cost_str}\n效果：{desc}\n",
    "query_quest_header": "🏆 对决任务/奖励：【{name}】 ({rname})",
    "query_quest_detail": "类型：{ctype} | 消耗: {cost_str}\n描述：{desc}\n",
    "victory_announcement": "🏆 恭喜玩家【{winner_name}】获得了最终胜利！对方领主生命值已归零！获得 2000 GP！",
    "defeat_private_tip": "☠️ 你的生命值已归零，你输了。",
    "duel_action_in_battle_only": "❌ 对战进行中，只能使用局内对决指令（如：使用、随从、进化、结束、幸运币）或输入帮助指令查看指南。",
    "duel_action_unknown": "❌ 未知动作指令。输入帮助指令可查看操作提示。",
    "duel_cmd_unknown": "❌ 未知的对决指令，请输入帮助指令获取教程。",
    "help_text": (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚔️ 【对决模式 (Duel) 指令帮助手册】\n"
        "对决模式是完全独立于肉鸽模式的双人 TCG 卡牌对决系统。\n\n"
        "💡 [局外/系统指令] (前缀支持 .duel 或 /duel)：\n"
        "• 发起对决：.duel invite @对方\n"
        "• 接受对决：.duel accept\n"
        "• 开启/关闭个人免前缀对决模式：.duel mode\n"
        "• 直接认输：.duel abandon\n"
        "• 牌组管理：.duel deck <子指令>\n"
        "  - 创建牌组：create <名称>\n"
        "  - 选择牌组：select <序号/名称>\n"
        "  - 牌组详情：info\n"
        "  - 添加卡牌：add <卡牌名> [数量]\n"
        "  - 移除卡牌：remove <详情序号> [数量]\n"
        "  - 导出牌组：export [序号/名称]\n"
        "  - 导入牌组：import <分享码> [新名称]\n\n"
        "⚔️ [局内对局动作] (仅在你的回合生效)：\n"
        "• 查看状态：.duel s\n"
        "• 使用卡牌：.duel p <手牌序号> [目标格子]\n"
        "  (注：物理或法术伤害牌默认只能以敌方随从格子 e2-e7 为目标，有 face_target 词条 of 直伤卡方可打领主 e1)\n"
        "• 随从攻击：.duel m <我方格子> a [敌方格子]\n"
        "  (注：进场首回合随从无法立即攻击，突进/冲锋词条除外，未指定目标默认打敌方第一个存活随从/领主)\n"
        "• 进化卡牌：.duel ev <我方格子/手牌序号>\n"
        "  (注：第 3 回合起解禁，每回合可进化一次，随从生命补满且攻血+2，护符进化不减吟唱)\n"
        "• 使用幸运币：.duel coin\n"
        "  (注：仅后手机会获得 2 个幸运币，使用不占手牌，本回合动作点 A+1)\n"
        "• 结束回合：.duel e\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
}
