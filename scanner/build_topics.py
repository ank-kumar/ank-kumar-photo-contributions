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
    "Aviation": ["aircraft", "airplane", "aeroplane", "airliner", "airbus", "boeing", "concorde", "helicopter",
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
    "Sports": ["roland garros", "stade roland garros", "grand slam", "fifa world football museum", "switzerland vs", "vs england", "football museum", "athletics", "stadium", "football", "soccer", "fifa", "uefa", "ballon", "camp nou", "san siro", "arsenal",
               "liverpool fc", "manchester city", "cricket", "lord s", "olympic", "olympics", "tennis", "golf",
               "bodybuilding", "arnold classic", "bernabeu", "allianz arena", "etihad", "sports", "hungaroring",
               "formula one", "racing", "world cup", "fa cup", "club", "rugby", "ice hockey"],
    "Architecture": ["memorial", "quarter", "cityscape", "stadthaus", "opernhaus", "technopark", "forum romanum", "landesmuseum", "church", "cathedral", "basilica", "mosque", "temple", "tower", "skyscraper", "building",
                     "bridge", "palace", "castle", "station", "square", "piazza", "platz", "monument", "gate", "dome",
                     "pantheon", "colosseum", "architecture", "chapel", "abbey", "synagogue", "parliament",
                     "bundeshaus", "reichstag", "fountain", "arch", "ruins", "hall", "facade", "tram stop"],
    "Museums": ["liverpool fc museum", "olympic museum", "musee olympique", "museum", "museums", "museo", "musee", "exhibition", "gallery", "collection", "experience"],
    "Art": ["art", "painting", "sculpture", "statue", "fresco", "mural", "artwork", "street art", "east side gallery",
            "giger", "xenomorph", "installation", "kunst", "bust", "relief", "graffiti"],
    "Music": ["music", "concert", "festival", "techno", "opera", "awakenings", "gashouder", "orchestra", "band",
              "beatles", "dj", "guitar", "musician", "jazz", "rock"],
    "Nature": ["twelve apostles", "aerial photograph", "lake", "mountain", "mountains", "alps", "alpine", "beach", "sea", "ocean", "river", "waterfall",
               "forest", "sunset", "sunrise", "glacier", "reef", "island", "bay", "garden", "snow", "landscape",
               "valley", "cliff", "cliffs", "kulm", "peak", "coast", "nature", "wildlife", "bird", "birds", "flowers"],
    "Trains": ["train", "trains", "tram", "trams", "railway", "railroad", "bahnhof", "hauptbahnhof", "metro",
               "subway", "underground", "locomotive", "glacier express", "sbb", "tramways", "rail", "railcar",
               "carriage", "platform", "signal box", "funicular", "cogwheel"],
    "Transport": ["bus", "buses", "coach", "ship", "boat", "boats", "cruise", "ferry", "cable car", "gondola lift",
                  "taxi", "bicycle", "bike", "scooter", "truck", "lorry", "port", "harbour", "harbor", "transport",
                  "transit", "zvv", "quay", "terminal", "pier"],
    "Religion": ["church", "cathedral", "basilica", "mosque", "temple", "chapel", "abbey", "synagogue", "vatican",
                 "monastery", "shrine", "religious", "pope", "saint", "st peter", "sacred", "crypt", "grossmunster"],
    "Movies": ["movie", "movies", "film", "films", "cinema", "harry potter", "warner bros", "hogwarts", "james bond",
               "007", "batmobile", "alien", "xenomorph", "avenue of stars", "garden of stars", "bruce lee",
               "film festival", "film awards", "hollywood", "bollywood", "star wars"],
    "Comics": ["comic", "comics", "comic strip", "comic book", "tintin", "smurfs", "manga", "marvel", "superhero",
               "asterix", "lucky luke"],
    "Finance": ["swiss life", "zurich insurance", "banks in", "bank", "banking", "ubs", "credit suisse", "julius bar", "julius baer", "kantonalbank", "raiffeisen",
                "paradeplatz", "bahnhofstrasse", "stock exchange", "bourse", "swiss exchange", "finance", "financial",
                "swiss national bank", "national bank", "insurance", "swiss re", "wealth management", "banknote",
                "currency", "coin", "coins", "money", "fintech", "headquarters of", "hsbc", "bnp", "deutsche bank"],
    "Universities": ["university", "universitat", "universite", "universita", "eth zurich", "eth zentrum", "epfl",
                     "college", "campus", "institute of technology", "faculty", "polytechnic", "academy",
                     "lecture hall", "school of", "manipal", "hochschule", "alumni", "research institute"],
    "People": ["portrait", "portraits", "people", "crowd", "spectators", "visitors", "cosplay", "cosplayer",
               "performer", "dancer", "protest", "demonstration", "rally", "pedestrians", "passers by", "audience"],
    "Wildlife": ["wildlife", "animal", "animals", "bird", "birds", "fish", "coral", "turtle", "kangaroo", "koala",
                 "shark", "whale", "dolphin", "zoo", "aquarium", "butterfly", "insect", "reptile", "penguin", "swan",
                 "duck", "deer", "fauna", "marine life"],
    "Motorsports": ["formula one", "formula 1", "grand prix", "hockenheimring", "nurburgring", "monza", "silverstone",
                    "hungaroring", "circuit", "racetrack", "race track", "autodromo", "dtm", "le mans", "rally",
                    "motorsport", "motorsports", "pit lane", "paddock", "spa francorchamps", "goodwood", "montmelo",
                    "racing car", "race car", "qualifying", "pole position"],
    "Olympics": ["olympic", "olympics", "olympia", "olympisch", "international olympic committee", "olympic museum",
                 "paralympic", "olympic torch", "olympic rings", "olympic stadium"],
    "Physics": ["cern", "lhc", "large hadron collider", "particle", "accelerator", "synchrocyclotron", "cyclotron",
                "physics", "quantum", "einstein", "collider", "antimatter", "detector", "atlas experiment",
                "cms experiment", "globe of science", "nuclear research"],
    "Technology": ["technopark", "vintage computer festival", "observation wheel", "technology", "computer", "server", "data center", "datacentre", "data centre", "robot",
                   "robotics", "electronics", "semiconductor", "satellite", "rocket", "spacecraft", "nasa", "isro",
                   "drone", "laboratory", "innovation", "microchip", "supercomputer", "engineering", "telescope",
                   "polar satellite launch vehicle", "pslv"],
    "Ocean": ["ocean", "sea", "reef", "coral", "beach", "underwater", "marine", "harbour", "harbor", "bay", "coast",
              "coastline", "wave", "waves", "lagoon", "barrier reef", "seaside", "shore", "tide", "snorkel"],
    "Mountains": ["mountain", "mountains", "alps", "alpine", "peak", "summit", "glacier", "jungfrau", "schilthorn",
                  "matterhorn", "eiger", "uetliberg", "harder kulm", "titlis", "mount pilatus", "rigi", "ridge",
                  "hiking", "trail", "valley", "massif", "gornergrat", "first cliff walk"],
    "Streets": ["street", "streets", "strasse", "avenue", "boulevard", "roadway", "alley", "promenade", "sidewalk",
                "pedestrian zone", "street scene", "old town", "altstadt", "gasse", "quai", "crossing", "zebra"],
    "Fitness": ["fitness", "gym", "bodybuilding", "bodybuilder", "mr olympia", "arnold classic", "workout", "muscle",
                "weightlifting", "weight lifting", "marathon", "triathlon", "athlete", "training session"],
    "Scuba Diving": ["scuba", "diving", "diver", "divers", "snorkelling", "snorkeling", "freediving", "free diving",
                     "dive site", "wreck dive", "underwater photography"],
    "Food": ["food", "restaurant", "cafe", "coffee", "chocolate", "cheese", "fondue", "wine", "beer", "brewery",
             "bakery", "cuisine", "dessert", "ice cream", "kitchen", "pub", "street food", "market hall", "confiserie"],
    "Events": ["festival", "parade", "carnival", "expo", "ceremony", "conference", "summit", "street parade",
               "christmas market", "celebration", "anniversary", "opening ceremony", "trade fair", "motor show",
               "world economic forum", "fasnacht"],
    "Luxury": ["luxury", "watch", "watches", "rolex", "omega", "patek", "swatch", "tag heuer", "jewellery", "jewelry",
               "boutique", "yacht", "grand hotel", "dolder", "five star", "designer", "fashion", "couture",
               "first class", "private jet"],
    "United Nations": ["united nations", "palais des nations", "un office", "unog", "unicef", "unhcr",
                       "world health organization", "world trade organization", "broken chair", "league of nations",
                       "international labour", "un geneva", "nations unies"],
    "Night": ["night", "at night", "night view", "night views", "nocturnal", "illuminated",
              "after dark", "dusk", "evening", "night photography", "lights at night"],
    "Cityscapes": ["cityscape", "skyline", "quarter", "quartier", "neighbourhood", "neighborhood",
                   "friesstrasse", "seebach", "oerlikon", "escher wyss", "industriequartier",
                   "zuri west", "aerial view", "aerial views", "panorama", "rooftop view",
                   "city view", "urban"],
    "Austria": ["austria", "austrian", "osterreich", "vienna", "wien", "salzburg", "innsbruck", "hallstatt",
                "tyrol", "tirol", "graz", "hangar 7", "red bull ring", "salzkammergut"],
    "Thailand": ["thailand", "thai", "bangkok", "phuket", "pattaya", "chiang mai", "krabi", "ayutthaya",
                 "wat arun", "wat pho", "grand palace bangkok"],
    "Denmark": ["denmark", "danish", "copenhagen", "kobenhavn", "nyhavn", "little mermaid", "tivoli gardens",
                "oresund", "aarhus"],
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
          "Hungary": "Europe", "Austria": "Europe", "Denmark": "Europe", "Thailand": "Asia", "Turkey": "Europe", "Hong Kong": "Asia", "Macau": "Asia", "Singapore": "Asia"}

def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " " + re.sub(r"[^a-z0-9]+", " ", s) + " "

def variants(k):
    """A keyword and its plural, so 'building' also matches 'Buildings in Oerlikon'."""
    k = norm(k)
    out = {k}
    stem = k.rstrip()
    out.add(stem + "s ")
    if stem.endswith("y"):
        out.add(stem[:-1] + "ies ")
    if stem.endswith(("s", "x", "ch", "sh")):
        out.add(stem + "es ")
    return out

KW = {t: sorted(set().union(*(variants(k) for k in kws))) for t, kws in TOPICS.items()}

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

json.dump(cats, open(f"{DATA}/commons_categories.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"Saved {sum(len(v) for v in cats.values()):,} category memberships "
      f"({len(set(c for v in cats.values() for c in v)):,} distinct) to data/commons_categories.json")

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
