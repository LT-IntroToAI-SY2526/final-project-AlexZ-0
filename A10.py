import html
import re, string, calendar, requests, time
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
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
# def get_flag(flag: str) -> str:
#     infobox_text = clean_text(get_first_infobox_text(get_page_html(flag)))
#     pattern = r"\s*(.*?)\n"
#     error_text = "Page has no info on wars it was used in"
#     match = get_match(infobox_text, pattern, error_text)
#     return match.group(1)

# below are a set of actions. Each takes a list argument and returns a list of answers
# according to the action and the argument. It is important that each function returns a
# list of the answer(s) and not just the answer itself.

def birth_date(matches: List[str]) -> List[str]:
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

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wikipedia Chatbot</title>
    <style>
        body {{ font-family: Arial, Helvetica, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
        h1 {{ color: #2c3e50; }}
        input[type=text] {{ width: 100%; padding: 8px; margin: 8px 0; box-sizing: border-box; font-size: 1rem; }}
        button {{ padding: 10px 16px; font-size: 1rem; cursor: pointer; }}
        .answer {{ background: #f6f8fa; border: 1px solid #dfe3e6; padding: 14px; margin: 12px 0; white-space: pre-wrap; }}
        .footer {{ color: #666; margin-top: 24px; font-size: 0.95rem; }}
    </style>
</head>
<body>
    <h1>Wikipedia Chatbot</h1>
    <form action="/" method="get">
        <label for="examples">Choose a example:</label>
        <select id="examples" onchange="fillExample()">
            <option value="">-- select an example --</option>
            <option value="when was grace hopper born">when was % born</option>
            <option value="what is the polar radius of earth">what is the polar radius of %</option>
            <option value="infobox python (programming language)">infobox %</option>
            <option value="conservation status giant panda">conservation status %</option>
            <option value="what are the symptoms of influenza">what are the symptoms of %</option>
            <option value="what is the population of canada">what is the population of %</option>
            <option value="where was the ak-47 used">where was % used</option>
            <option value="what is the hardness of quartz">what is the hardness of %</option>
        </select>
        <label for="q">Ask a question:</label>
        <input id="q" name="q" type="text" placeholder="when was grace hopper born" autofocus value="$query">
        <button type="submit">Ask</button>
    </form>
    $answer_html
    <div class="footer">Hint: try questions like "when was % born" or "what is the polar radius of %".</div>
    <script>
        function fillExample() {
            const select = document.getElementById('examples');
            const query = document.getElementById('q');
            if (select.value) {
                query.value = select.value;
                query.focus();
            }
        }
    </script>
</body>
</html>
"""

def render_html(query: str = "", answers: List[str] = None) -> bytes:
    answer_html = ""
    if answers is not None:
        if answers:
            answer_html = "".join(f"<div class=\"answer\">{html.escape(ans)}</div>" for ans in answers)
        else:
            answer_html = "<div class=\"answer\">No answers</div>"
    return string.Template(HTML_TEMPLATE).substitute(
        query=html.escape(query),
        answer_html=answer_html,
    ).encode("utf-8")


class WikiChatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/favicon.ico"):
            self.send_response(404)
            self.end_headers()
            return

        parsed = urllib.parse.urlparse(self.path)
        query = ""
        answers = None
        if parsed.query:
            params = urllib.parse.parse_qs(parsed.query)
            query_list = params.get("q", [""])
            query = query_list[0].strip()
            if query:
                normalized = query.replace("?", "").lower().split()
                try:
                    answers = search_pa_list(normalized)
                except Exception:
                    answers = [f"Could not find any info for '{query}'."]

        content = render_html(query=query, answers=answers)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        return


def run_web_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    url = f"http://{host}:{port}/"
    server = HTTPServer((host, port), WikiChatHandler)
    print(f"Starting Wikipedia chatbot web server at {url}")
    print("Press Ctrl+C to stop.")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    server.serve_forever()


if __name__ == "__main__":
    if "--web" in sys.argv or "web" in sys.argv:
        run_web_server()
    else:
        query_loop()
