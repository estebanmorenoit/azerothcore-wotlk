-- "Charged Rift Gem" (item 7249) drops from "Miners' League Crates" (loot
-- entry 1677) with QuestRequired = 1, but no quest_template row anywhere in
-- this database references item 7249 as a required item or item drop. The
-- server's loot code (LootMgr.cpp) can only mark the item takeable if the
-- looter has an active quest needing it; since no such quest exists, that
-- check always fails, and the item is sent to the loot window permanently
-- locked (LOOT_SLOT_TYPE_LOCKED) instead of never being shown at all -
-- visible, but impossible to pick up, for every player, every time.
--
-- No quest in this database plausibly matches it either (checked every
-- quest with "Miners", "Rift", or "League" in its title), so this clears
-- the orphaned QuestRequired flag instead of guessing at a missing quest
-- link - the item becomes normal takeable loot.
DELETE FROM `gameobject_loot_template` WHERE `Entry` = 1677 AND `Item` = 7249;
INSERT INTO `gameobject_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(1677, 7249, 0, 100, 0, 1, 0, 1, 1, 'Miners\' League Crates - Charged Rift Gem');
