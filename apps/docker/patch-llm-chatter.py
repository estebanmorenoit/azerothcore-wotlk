#!/usr/bin/env python3
# NOT CALLED from build-images.yml as of 2026-09-14 — upstream fixed this
# themselves (Hokken/mod-llm-chatter@master's SendPartyMessageInstant() now
# calls BuildChatPacket with the correct 8-arg overload matching this core's
# Chat.h, confirmed by diffing the two). Kept for reference in case it
# regresses; re-add the "Patch known mod-llm-chatter compile bug" step in
# build-images.yml pointing at this script if the build ever fails the same
# way again.
#
# Originally: mod-llm-chatter's upstream SendPartyMessageInstant() called
# ChatHandler::BuildChatPacket() with an argument order from an older
# AzerothCore signature, which failed to compile against this core (see
# wow-server-playerbots README's "Known upstream issue in mod-llm-chatter").
# Regex (not exact string match) so minor upstream whitespace changes don't
# silently break this — a real signature/argument change should still fail
# loudly via the count check below.
import re
import sys

path = "modules/mod-llm-chatter/src/LLMChatterShared.cpp"

with open(path) as f:
    content = f.read()

pattern = re.compile(
    r"ChatHandler::BuildChatPacket\(\s*"
    r"data,\s*"
    r"CHAT_MSG_PARTY,\s*"
    r"message,\s*"
    r"LANG_UNIVERSAL,\s*"
    r"CHAT_TAG_NONE,\s*"
    r"bot->GetGUID\(\),\s*"
    r"bot->GetName\(\)\);",
    re.MULTILINE,
)

new_content, count = pattern.subn(
    "ChatHandler::BuildChatPacket(data, CHAT_MSG_PARTY, LANG_UNIVERSAL, bot, bot, message);",
    content,
    count=1,
)

if count != 1:
    sys.exit(
        f"Expected exactly 1 match for the known broken BuildChatPacket call, found {count} "
        "— upstream may have changed the surrounding code, check manually before re-running."
    )

with open(path, "w") as f:
    f.write(new_content)

print("Patched BuildChatPacket call in LLMChatterShared.cpp")
