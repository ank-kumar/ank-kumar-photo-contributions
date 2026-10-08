#!/usr/bin/env python3
"""Tag each photo in use with topics and regions from its filename, Commons caption and Commons categories."""
import csv, json, re, time, unicodedata, urllib.parse, urllib.request
from collections import Counter

DATA = "/Users/ank/projects/image-reuse-tracker/data"
UA = {"User-Agent": "ImageReuseTracker/0.7 (https://commons.wikimedia.org/wiki/User:Ank_gsx) python-urllib"}
TOPICS = {
    "Switzerland": ["switzerland", "swiss", "schweiz", "zurich", "geneva", "geneve", "basel", "bern", "lucerne", "luzern",
                    "interlaken", "dubendorf", "payerne", "lausanne", "schilthorn", "jungfrau", "zermatt", "davos",
                    "oerlikon", "st gallen", "biel", "bienne", "montreux", "lugano", "romanshorn", "altdorf", "kloten",
                    "dietikon", "harder kulm", "murren", "grindelwald", "chillon", "winterthur", "rapperswil"],
    "Germany": ["germany", "german", "deutschland", "berlin", "munich", "munchen", "stuttgart", "frankfurt", "hamburg",
                "sinsheim", "speyer", "hockenheim", "hockenheimring", "cologne", "koln", "bavaria", "dresden",
                "nuremberg", "heidelberg", "nurburgring", "reichstag", "bundestag", "brandenburg gate"],
    "The UK": ["london", "england", "manchester", "liverpool", "birmingham", "scotland", "edinburgh", "united kingdom",
               "british", "wales", "silverstone", "goodwood", "stratford", "oxford", "cambridge", "brighton"],
    "Italy": ["italy", "italian", "italia", "rome", "roma", "vatican", "milan", "milano", "monza", "venice", "florence",
              "naples", "turin", "torino", "pisa", "colosseum", "pantheon", "san siro", "maranello"],
    "India": ["india", "indian", "bengaluru", "bangalore", "jamshedpur", "mumbai", "delhi", "kolkata", "chennai",
              "hyderabad", "jharkhand", "karnataka", "goa", "kerala", "pune", "agra", "rupee"],
    "Europe": ["europe", "european", "france", "paris", "spain", "barcelona", "madrid", "netherlands", "amsterdam",
               "belgium", "brussels", "bruges", "austria", "vienna", "salzburg", "hungary", "budapest", "czech",
               "prague", "portugal", "lisbon", "greece", "athens", "poland", "denmark", "copenhagen", "sweden",
               "stockholm", "norway", "finland", "croatia", "istanbul", "turkey", "turkiye", "monaco", "luxembourg",
               "camp nou", "catalonia", "mogyorod", "hungaroring"],
    "Asia": ["asia", "hong kong", "hongkong", "macau", "macao", "china", "chinese", "singapore", "japan", "tokyo",
             "dubai", "emirates", "abu dhabi", "thailand", "bangkok", "malaysia", "kuala lumpur", "sri lanka", "nepal",
             "korea", "vietnam", "qatar", "doha", "kowloon", "taiwan"],
    "Australia": ["australia", "australian", "sydney", "melbourne", "cairns", "queensland", "byron bay",
                  "great ocean road", "twelve apostles", "12 apostles", "apollo bay", "bondi", "new south wales",
                  "gold coast", "brisbane", "tasmania", "great barrier reef", "perth", "adelaide"],
    "Airplanes": ["aircraft", "airplane", "aeroplane", "airliner", "airbus", "boeing", "concorde", "helicopter",
                  "air force", "airshow", "air show", "air14", "airport", "flughafen", "fighter", "rafale", "mirage",
                  "mig", "hawker", "pilatus", "fliegerstaffel", "aviation", "airline", "cessna", "glider", "tupolev",
                  "marut", "ajeet", "gnat", "super puma", "spitfire", "aerospace", "patrouille suisse", "f a 18",
                  "fighting falcon", "tiger ii", "eurofighter", "gripen", "lockheed", "dassault", "eurocopter",
                  "airship", "zeppelin", "flying bulls", "hangar 7", "aerobatic"],
    "Military": ["military", "army", "air force", "navy", "naval", "missile", "tank", "war", "battle", "bunker",
                 "fighter", "bomber", "weapon", "artillery", "ordnance", "soldier", "defence", "defense", "stinger",
                 "memorial park", "flab", "armoured", "armored", "warship", "fuhrerbunker", "canberra"],
    "Automobiles": ["car", "cars", "ferrari", "lamborghini", "bugatti", "porsche", "mclaren", "aston martin",
                    "koenigsegg", "mercedes", "bmw", "audi", "jaguar", "motor show", "gims", "grand basel", "auto",
                    "autos", "supercar", "hypercar", "racing", "formula one", "formula 1", "dtm", "rally", "chevrolet",
                    "ford", "honda", "toyota", "pagani", "zenvo", "maserati", "alfa romeo", "rolls royce", "bentley",
                    "tesla", "vehicle", "roadster", "convertible", "coupe", "mahindra", "volkswagen", "lotus",
                    "batmobile", "autobau", "chelsea auto legends", "top gear", "hennessey", "rimac", "fenyr"],
    "Sports": ["stadium", "football", "soccer", "fifa", "uefa", "ballon", "camp nou", "san siro", "arsenal",
               "liverpool fc", "manchester city", "cricket", "lord s", "olympic", "olympics", "tennis", "golf",
               "bodybuilding", "arnold classic", "bernabeu", "allianz arena", "etihad", "sports", "hungaroring",
               "formula one", "racing", "world cup", "fa cup", "club", "rugby", "ice hockey"],
    "Architecture": ["church", "cathedral", "basilica", "mosque", "temple", "tower", "skyscraper", "building",
                     "bridge", "palace", "castle", "station", "square", "piazza", "platz", "monument", "gate", "dome",
                     "pantheon", "colosseum", "architecture", "chapel", "abbey", "synagogue", "parliament",
                     "bundeshaus", "reichstag", "fountain", "arch", "ruins", "hall", "facade", "tram stop"],
    "Museums": ["museum", "museums", "museo", "musee", "exhibition", "gallery", "collection", "experience"],
    "Art": ["art", "painting", "sculpture", "statue", "fresco", "mural", "artwork", "street art", "east side gallery",
            "giger", "xenomorph", "installation", "kunst", "bust", "relief", "graffiti"],
    "Music": ["music", "concert", "festival", "techno", "opera", "awakenings", "gashouder", "orchestra", "band",
              "beatles", "dj", "guitar", "musician", "jazz", "rock"],
    "Nature": ["lake", "mountain", "mountains", "alps", "alpine", "beach", "sea", "ocean", "river", "waterfall",
               "forest", "sunset", "sunrise", "glacier", "reef", "island", "bay", "garden", "snow", "landscape",
               "valley", "cliff", "cliffs", "kulm", "peak", "coast", "nature", "wildlife", "bird", "birds", "flowers"],
    "Trains & transport": ["train", "tram", "railway", "railroad", "station", "bahnhof", "hauptbahnhof", "metro",
                           "subway", "bus", "ship", "boat", "boats", "cruise", "ferry", "locomotive", "glacier express",
                           "sbb", "zvv", "tramways", "cable car", "funicular"],
    "Religion": ["church", "cathedral", "basilica", "mosque", "temple", "chapel", "abbey", "synagogue", "vatican",
                 "monastery", "shrine", "religious", "pope", "saint", "st peter", "sacred", "crypt", "grossmunster"],
    "Movies": ["movie", "movies", "film", "films", "cinema", "harry potter", "warner bros", "hogwarts", "james bond",
               "007", "batmobile", "alien", "xenomorph", "avenue of stars", "garden of stars", "bruce lee",
               "film festival", "film awards", "hollywood", "bollywood", "star wars"],
    "Comics": ["comic", "comics", "comic strip", "comic book", "tintin", "smurfs", "manga", "marvel", "superhero",
               "asterix", "lucky luke"],
    "Zurich": ["zurich", "oerlikon", "limmat", "limmatquai", "grossmunster", "fraumunster", "lindenhof",
               "bahnhofstrasse", "paradeplatz", "burkliplatz", "utoquai", "hardbrucke", "altstetten", "uetliberg",
               "felsenegg", "landesmuseum", "friesstrasse", "hallenstadion", "dolder", "kloten", "dubendorf", "glatt"],
    "Vatican": ["vatican", "st peter", "saint peter", "sistine", "musei vaticani", "pope", "holy see"],
    "Holland": ["netherlands", "dutch", "holland", "amsterdam", "rotterdam", "the hague", "utrecht", "gashouder",
                "anne frank", "heineken", "i amsterdam", "keukenhof", "delft"],
    "Belgium": ["belgium", "belgian", "brussels", "bruges", "brugge", "antwerp", "ghent", "manneken pis", "atomium",
                "berlaymont", "mont des arts", "liege"],
    "Czech Republic": ["czech", "prague", "praha", "brno", "bohemia", "charles bridge"],
    "France": ["france", "french", "paris", "lyon", "marseille", "nice", "eiffel", "louvre", "versailles",
               "invalides", "champ de mars", "strasbourg", "alsace"],
    "Spain": ["spain", "spanish", "barcelona", "madrid", "catalonia", "catalunya", "sagrada familia", "gaudi",
              "camp nou", "seville", "valencia", "bernabeu", "montmelo"],
    "Hungary": ["hungary", "hungarian", "budapest", "hungaroring", "mogyorod", "fisherman s bastion"],
    "Turkey": ["turkey", "turkiye", "istanbul", "bosphorus", "hagia sophia", "ankara", "cappadocia", "grand bazaar"],
    "Hong Kong": ["hong kong", "hongkong", "kowloon", "victoria harbour", "tsim sha tsui", "repulse bay", "lantau",
                  "peak tram"],
    "Macau": ["macau", "macao"],
    "Singapore": ["singapore", "marina bay", "merlion", "sentosa"],
    "Scotland": ["scotland", "scottish", "edinburgh", "glasgow", "highlands", "loch"],
}
PARENT = {"Switzerland": "Europe", "Germany": "Europe", "The UK": "Europe", "Italy": "Europe", "India": "Asia",
          "Zurich": "Switzerland", "Scotland": "The UK", "Vatican": "Europe", "Holland": "Europe",
          "Belgium": "Europe", "Czech Republic": "Europe", "France": "Europe", "Spain": "Europe",
          "Hungary": "Europe", "Turkey": "Europe", "Hong Kong": "Asia", "Macau": "Asia", "Singapore": "Asia"}

def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " " + re.sub(r"[^a-z0-9]+", " ", s) + " "

KW = {t: [norm(k) for k in kws] for t, kws in TOPICS.items()}

def get(params):
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params), headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=60))

files = json.load(open(f"{DATA}/commons_files.json", encoding="utf-8"))
captions = json.load(open(f"{DATA}/captions.json", encoding="utf-8"))
cats = {}
print(f"Fetching Commons categories for {len(files)} photos...")
for i in range(0, len(files), 50):
    p = {"action": "query", "format": "json", "prop": "categories", "cllimit": "max", "clshow": "!hidden",
         "titles": "|".join("File:" + f for f in files[i:i + 50])}
    while True:
        d = get(p)
        for pg in d.get("query", {}).get("pages", {}).values():
            cats.setdefault(pg["title"].removeprefix("File:"), []).extend(
                c["title"].removeprefix("Category:") for c in pg.get("categories", []))
        if "continue" not in d:
            break
        p.update(d["continue"])
        time.sleep(1)
    if (i // 50) % 20 == 19 or i + 50 >= len(files):
        print(f"  {min(i + 50, len(files))}/{len(files)}")
    time.sleep(1)

topics = {}
for f in files:
    text = norm(" ".join([f, captions.get(f, ""), " ".join(cats.get(f, []))]))
    t = {name for name, kws in KW.items() if any(k in text for k in kws)}
    for _ in range(2):
        t |= {PARENT[x] for x in t if x in PARENT}
    topics[f] = sorted(t)
json.dump(topics, open(f"{DATA}/topics.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

counts = Counter(t for ts in topics.values() for t in ts)
print("\nPhotos per topic:")
for t, n in counts.most_common():
    print(f"  {n:4d}  {t}")
print(f"  {sum(1 for ts in topics.values() if not ts):4d}  (no topic)")
