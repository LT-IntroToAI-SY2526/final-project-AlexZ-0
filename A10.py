import re, string, calendar, requests, time
from wikipedia import WikipediaPage
import wikipedia
from bs4 import BeautifulSoup
from match import match
from typing import List, Callable, Tuple, Any, Match
import random


def get_page_html(title: str) -> str:
    for attempt in range(5):
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "redirects": True,
            },
            headers={"User-Agent": "intro-ai-class/1.0"}
        )
        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 5))
            print(f"Rate limited — waiting {wait}s before retrying '{title}'...")
            time.sleep(wait)
            continue
        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if "error" not in data:
                time.sleep(2)  # polite delay after every successful call
                return data["parse"]["text"]["*"]
    raise ConnectionError(f"Could not retrieve Wikipedia page for '{title}' after 5 attempts")


def get_first_infobox_text(html: str) -> str:
    """Gets first infobox html from a Wikipedia page (summary box)

    Args:
        html - the full html of the page

    Returns:
        html of just the first infobox
    """
    soup = BeautifulSoup(html, "html.parser")
    results = soup.find_all(class_="infobox")

    if not results:
        raise LookupError("Page has no infobox")
    return results[0].text


def clean_text(text: str) -> str:
    """Cleans given text removing non-ASCII characters and duplicate spaces & newlines

    Args:
        text - text to clean

    Returns:
        cleaned text
    """
    only_ascii = "".join([char if char in string.printable else " " for char in text])
    no_dup_spaces = re.sub(" +", " ", only_ascii)
    no_dup_newlines = re.sub("\n+", "\n", no_dup_spaces)
    return no_dup_newlines


def get_match(
    text: str,
    pattern: str,
    error_text: str = "Page doesn't appear to have the property you're expecting",
) -> Match:
    """Finds regex matches for a pattern

    Args:
        text - text to search within
        pattern - pattern to attempt to find within text
        error_text - text to display if pattern fails to match

    Returns:
        text that matches
    """
    p = re.compile(pattern, re.DOTALL | re.IGNORECASE)
    match = p.search(text)

    if not match:
        raise AttributeError(error_text)
    return match

def get_polar_radius(planet_name: str) -> str:
    """Gets the radius of the given planet

    Args:
        planet_name - name of the planet to get radius of

    Returns:
        radius of the given planet
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(planet_name)))
    pattern = r"(?:Polar radius|Mean radius)(?:[^\d]*)(?P<radius>[\d,.]+)(?:.*?)km"
    error_text = "Page infobox has no polar radius information"
    match = get_match(infobox_text, pattern, error_text)

    return match.group("radius")

def get_birth_date(name: str) -> str:
    """Gets birth date of the given person

    Args:
        name - name of the person

    Returns:
        birth date of the given person
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"(?:Born\D*)(?P<birth>\d{4}-\d{2}-\d{2})"
    error_text = (
        "Page infobox has no birth information (at least none in xxxx-xx-xx format)"
    )
    match = get_match(infobox_text, pattern, error_text)

    return match.group("birth")

def show_infobox(matches: List[str]) -> List[str]:
    title = " ".join(matches)
    html = get_page_html(title)
    info = get_first_infobox_text(html)
    return [clean_text(info)]

def get_endangered(name: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"Conservation status\s*(.+?)\n"
    error_text = "Page has no info on endangered status"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)
def get_symptoms(sickness: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(sickness)))
    pattern = r"Symptoms\s*(.*?)Complications"
    error_text = "Page has no info on symptoms"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)
def get_population(state: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(state)))
    pattern = r"Population.*?Total\s*([\d,]+)"
    error_text = "Page has no info on population"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)
def get_wars(gun: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(gun)))
    pattern = r"Wars\s*(.*?)\n"
    error_text = "Page has no info on wars it was used in"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)

def get_mohs_hardness_from_text(text: str) -> str:
    """Extract Mohs scale hardness values from a text block (simple regex).

    Returns the matched hardness string (e.g. "5.5 6" or "5.5-6").
    """
    pattern = r"Mohs.*?hardness\s*([0-9.\- ,]+)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        raise AttributeError("Page has no Mohs hardness info")
    return match.group(1).strip()

def get_mohs_hardness(name: str) -> str:
    """Fetch page infobox for `name` and extract Mohs hardness using a simple regex."""
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    return get_mohs_hardness_from_text(infobox_text)

def hardness_action(matches: List[str]) -> List[str]:
    """Action wrapper for the pattern-action list that returns a user-friendly answer."""
    name = " ".join(matches)
    try:
        value = get_mohs_hardness(name)
        return [f"Mohs scale hardness for {name.title()}: {value}"]
    except Exception as e:
        return [f"Could not find Mohs hardness for {name.title()}: {e}"]
def get_family(name: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"Family:\s*([A-Za-z]+)"
    error_text = "Page has no info on plant family"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)

# def get_flag(flag: str) -> str:
#     infobox_text = clean_text(get_first_infobox_text(get_page_html(flag)))
#     pattern = r"\s*(.*?)\n"
#     error_text = "Page has no info on wars it was used in"
#     match = get_match(infobox_text, pattern, error_text)
#     return match.group(1)
#Hangman
def play_hangman(dummy: List[str]) -> List[str]:
    """Starts a hangman game using a random U.S. state or city."""
    places = [
        "California", "Texas", "Florida", "New York",
        "Chicago", "Houston", "Phoenix", "Philadelphia",
        "San Antonio", "San Diego", "Dalla", "Moscow"
    ]

    secret = random.choice(places).lower()
    display = ["_" if c.isalpha() else c for c in secret]
    guessed = set()
    lives = 6

    print("\n🎮 Starting Hangman! Guess the U.S. state or city.")
    print("I’ll also give you a clue once you get close.\n")

    while lives > 0 and "_" in display:
        print("Word:", " ".join(display))
        print(f"Lives left: {lives}")
        print(f"Guessed letters: {', '.join(sorted(guessed))}\n")

        guess = input("Guess a letter: ").lower().strip()

        if not guess.isalpha() or len(guess) != 1:
            print("Please guess a single letter.\n")
            continue

        if guess in guessed:
            print("You already guessed that.\n")
            continue

        guessed.add(guess)

        if guess in secret:
            print("Correct!\n")
            for i, c in enumerate(secret):
                if c == guess:
                    display[i] = c
        else:
            print("Wrong!\n")
            lives -= 1

        # Give a clue when half the word is revealed
        if display.count("_") <= len(secret) // 2:
            try:
                clue = get_population(secret.title())
                print(f" Clue: Its population is around {clue}.\n")
            except:
                pass

    if "_" not in display:
        print(f"You win! The word was: {secret.title()}")
    else:
        print(f"Out of lives! The word was: {secret.title()}")

    return ["Game over"]

# below are a set of actions. Each takes a list argument and returns a list of answers
# according to the action and the argument. It is important that each function returns a
# list of the answer(s) and not just the answer itself.

def birth_date(matches: List[str]) -> List[str]:
    """Returns birth date of named person in matches

    Args:
        matches - match from pattern of person's name to find birth date of

    Returns:
        birth date of named person
    """
def family(matches: List[str]) -> List[str]:
    return [get_family(" ".join(matches))]

    return [get_birth_date(" ".join(matches))]
def endangered(matches: List[str]) -> List[str]:

    return [get_endangered(" ".join(matches))]
def wars(matches: List[str]) -> List[str]:

    return [get_wars(" ".join(matches))]
def symptoms(matches: List[str]) -> List[str]:

    return [get_symptoms(" ".join(matches))]
def population(matches: List[str]) -> List[str]:

    return [get_population(" ".join(matches))]
def polar_radius(matches: List[str]) -> List[str]:
    """Returns polar radius of planet in matches

    Args:
        matches - match from pattern of planet to find polar radius of

    Returns:
        polar radius of planet
    """
    return [get_polar_radius(matches[0])]


# dummy argument is ignored and doesn't matter
def bye_action(dummy: List[str]) -> None:
    raise KeyboardInterrupt


# type aliases to make pa_list type more readable, could also have written:
# pa_list: List[Tuple[List[str], Callable[[List[str]], List[Any]]]] = [...]
Pattern = List[str]
Action = Callable[[List[str]], List[Any]]

# The pattern-action list for the natural language query system. It must be declared
# here, after all of the function definitions
pa_list: List[Tuple[Pattern, Action]] = [
    ("when was % born".split(), birth_date),
    ("what is the polar radius of %".split(), polar_radius),
    ("infobox %".split(), show_infobox),
    ("conservation status %".split(), endangered),
    ("what are the symptoms of %".split(), symptoms),
    ("what is the population of %".split(), population),
    ("play hangman".split(), play_hangman),
    ("where was % used".split(), wars),
    ("what is the hardness of %".split(), hardness_action),
    (["bye"], bye_action),
]

def search_pa_list(src: List[str]) -> List[str]:
    """Takes source, finds matching pattern and calls corresponding action. If it finds
    a match but has no answers it returns ["No answers"]. If it finds no match it
    returns ["I don't understand"].

    Args:
        source - a phrase represented as a list of words (strings)

    Returns:
        a list of answers. Will be ["I don't understand"] if it finds no matches and
        ["No answers"] if it finds a match but no answers
    """
    for pat, act in pa_list:
        mat = match(pat, src)
        if mat is not None:
            answer = act(mat)
            return answer if answer else ["No answers"]

    return ["I don't understand"]


def query_loop() -> None:
    """The simple query loop. The try/except structure is to catch Ctrl-C or Ctrl-D
    characters and exit gracefully"""
    print("Welcome to the wikipedia chatbot!\n")
    while True:
        try:
            print()
            query = input("Your query? ").replace("?", "").lower().split()
            answers = search_pa_list(query)
            for ans in answers:
                print(ans)

        except (KeyboardInterrupt, EOFError):
            break

    print("\nSo long!\n")


# uncomment the next line once you've implemented everything are ready to try it out
query_loop()
