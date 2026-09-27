"""Messages that tactics treat as routine (no pause). The kernel also has
DEFAULT_BENIGN for pet chatter and common noises."""

# Routine messages that shouldn't interrupt exploring (the kernel already
# ignores pet chatter and common noises).
BENIGN = [
    r"^There is a (doorway|broken door|open door) here",
    r"^There are (several|many) objects here",
    r"^You find ",   # hidden things found are shown on the map
    r"^That door is closed\.",
    r"^The door resists!",
    r"^This door is locked\.",
    r"^This door is broken\.",
    r"^You have a (sad|strange) feeling for a moment",
    r"^A boulder blocks your path",
    r"^You try to move the boulder, but in vain\.",
    r"^Perhaps that's why you cannot move past it\.",
    r"blocks your path\.",
    r"^You are carrying too much to get through\.",
    r"^There is a (staircase|ladder) (up|down) here",
    r"^There is an? (fountain|altar|sink|throne|grave|tree) here",
    # engravings read when stepping on them (travel stops there; the text is still shown)
    r"^Something is written here in the (dust|frost)\.",
    r"^Something is engraved here on the ",
    r"^Some text has been (burned|melted) into the ",
    r"^There's some graffiti on the ",
    r"^You see a message scrawled in blood here\.",
    r"^You (read|feel the words): ",
]

