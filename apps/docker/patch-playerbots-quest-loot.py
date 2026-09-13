#!/usr/bin/env python3
# mod-playerbots' StoreLootAction::IsLootAllowed() lets a bot loot any item
# that matches one of ITS OWN active quests, with no regard for whether its
# master (the real player) is working the same quest and still needs that
# item too. Bots react within ~100ms (AiPlayerbot.ReactDelay), so on a
# shared open-world corpse that only carries a single copy of a quest item,
# the bot wins that race essentially every time — silently blocking the
# master's own quest progress, since quest-item credit requires physically
# holding the item.
#
# The intended fix was actually already sketched in this exact function,
# just commented out (see the removed lines below). Elsewhere in the same
# module (ItemUsageValue.cpp), the working, shipped pattern for "defer to
# master" is: `!IsSelfBot(bot) && master && syncQuestWithPlayer &&
# <master still needs item>` — this patch brings that same, already-proven
# pattern into the loot-gate function so the bot never picks the item up
# in the first place, rather than just not valuing it after the fact.
#
# Regex (not exact string match) so minor upstream whitespace changes don't
# silently break this — a real logic change should still fail loudly via
# the count check below.
import re
import sys

path = "modules/mod-playerbots/src/Ai/Base/Actions/LootAction.cpp"

with open(path) as f:
    content = f.read()

pattern = re.compile(
    r"    if \(proto->StartQuest\)\n"
    r"    \{\n"
    r"        return true;\n"
    r"    \}\n"
    r"\n"
    r"    for \(uint8 slot = 0; slot < MAX_QUEST_LOG_SIZE; \+\+slot\)\n"
    r"    \{\n"
    r"        uint32 entry = botAI->GetBot\(\)->GetQuestSlotQuestId\(slot\);\n"
    r"        Quest const\* quest = sObjectMgr->GetQuestTemplate\(entry\);\n"
    r"        if \(!quest\)\n"
    r"            continue;\n"
    r"\n"
    r"        for \(uint8 i = 0; i < 4; i\+\+\)\n"
    r"        \{\n"
    r"            if \(quest->RequiredItemId\[i\] == itemid\)\n"
    r"            \{\n"
    r"                // if \(AI_VALUE2\(uint32, \"item count\", proto->Name1\) < quest->RequiredItemCount\[i\]\)\n"
    r"                // \{\n"
    r"                //     if \(botAI->GetMaster\(\) && sPlayerbotAIConfig\.syncQuestWithPlayer\)\n"
    r"                //         return false; //Quest is autocomplete for the bot so no item needed\.\n"
    r"                // \}\n"
    r"\n"
    r"                return true;\n"
    r"            \}\n"
    r"        \}\n"
    r"    \}\n",
    re.MULTILINE,
)

replacement = """    if (proto->StartQuest)
    {
        return true;
    }

    // If our master still needs this exact item for one of their own active
    // quests, leave it on the corpse for them instead of racing to loot it
    // ourselves. Mirrors the same defer-to-master pattern already used in
    // ItemUsageValue.cpp for item-usage decisions.
    if (Player* master = botAI->GetMaster())
    {
        if (sPlayerbotAIConfig.syncQuestWithPlayer && !IsSelfBot(botAI->GetBot()))
        {
            for (uint8 slot = 0; slot < MAX_QUEST_LOG_SIZE; ++slot)
            {
                uint32 masterEntry = master->GetQuestSlotQuestId(slot);
                Quest const* masterQuest = sObjectMgr->GetQuestTemplate(masterEntry);
                if (!masterQuest)
                    continue;

                for (uint8 i = 0; i < 4; i++)
                {
                    if (masterQuest->RequiredItemId[i] == itemid &&
                        master->GetItemCount(itemid, false) < masterQuest->RequiredItemCount[i])
                    {
                        return false; // Master still needs this one — leave it for them
                    }
                }
            }
        }
    }

    for (uint8 slot = 0; slot < MAX_QUEST_LOG_SIZE; ++slot)
    {
        uint32 entry = botAI->GetBot()->GetQuestSlotQuestId(slot);
        Quest const* quest = sObjectMgr->GetQuestTemplate(entry);
        if (!quest)
            continue;

        for (uint8 i = 0; i < 4; i++)
        {
            if (quest->RequiredItemId[i] == itemid)
            {
                return true;
            }
        }
    }
"""

new_content, count = pattern.subn(replacement, content, count=1)

if count != 1:
    sys.exit(
        f"Expected exactly 1 match for the known IsLootAllowed quest-item block, found {count} "
        "— upstream may have changed the surrounding code, check manually before re-running."
    )

with open(path, "w") as f:
    f.write(new_content)

print("Patched StoreLootAction::IsLootAllowed to defer shared quest items to the master")
