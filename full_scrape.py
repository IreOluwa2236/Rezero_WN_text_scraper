import argparse
import requests
from bs4 import BeautifulSoup
import time
import re
import os 
import sys 
from urllib.parse import urlparse




START_URL = "https://witchculttranslation.com/table-of-content/"  
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Arcs")


REQUES_HEADERS = {
    "User-agent": (
        "Mozilla/5.0 (windows NT 10.0; win64; x64) Applewebkit/537.36 "
        "(KHTML, like Gecko) Chrome/ 120.0.0.0 Safari/537.36"
    ) 
}

SKIP_SUFFIXES = (".pdf",)
SKIP_DOMAINS = ("mega.nz",)

CONTENT_SELECTORS = [ 
    ("div", {"class": "entry-content"}), 
    ("div", {"class": "post-content"}), 
    ("div", {"class": "td-post-content"}), 
    ("div", {"class": "post-body"}), 
    ("div", {"class": "single-content"}),
    ("article",{}),
] 
REQUEST_DELAY_SECONDS = 1.5 

def sanatize_filename(name: str) -> str: 
    """ 
    Strip charachters that are'nt allowed in the filenames on Windows/Mac/Linux,
    and trim it to a sane length.  
    """

    name = re.sub(r'[\\/*?:"<>|]',"",name)
    name = re.sub(r"\s+"," ",name).strip() 
    return name[:150] 

def fetch_soup(url:str): 
    resp = requests.get(url,headers=REQUES_HEADERS,timeout=20) 
    resp.raise_for_status() 
    return BeautifulSoup(resp.text,"html.parser")  



def get_arc_plan(): 
    soup = fetch_soup(START_URL) 
    content_div = soup.find("div",class_="entry-content") 
    if content_div is None: 
        raise RuntimeError(
            "could not find 'entry-content' div on the TOC page. " 
            "The site's markup may have changed -- inspect the page HTML" 
        )
    all_headers= content_div.find_all("h1") 
    arc_headers = [
        h for h in all_headers
        if re.match(r"^\s*Arc\s+\d+",h.get_text(strip=True)) 
    ]

    if not arc_headers:
        raise RuntimeError(
            "No 'Arc N' headers found. Print the page HTML and check whether" \
            "arcs are still <h1> tags, or whether the class/structure changed."
        ) 
    arcs = [] 

    for i ,header in enumerate(arc_headers): 
        header_text = header.get_text(strip=True) 
        m = re.match(r"Arc\s+(\d+)\s*[---]\s*(.*)", header_text) 
        arc_num = int(m.group(1)) if m else i + 1
        arc_title = m.group(2).strip() if m else header_text 
        stop_node = arc_headers[i+1] if i +1<len(arc_headers) else None 
        chapters = [] 

        for sibling in header.find_all_next(): 
            if stop_node is not None and sibling is stop_node:
                break
            if sibling.name == "li": 
                a = sibling.find("a",href = True)
                if a: 
                    chap_title = a.get_text(strip=True) 
                    chap_Url = a["href"] 
                    chapters.append((chap_title,chap_Url)) 
        arcs.append({"arc_num":arc_num,"title":arc_title,"chapters":chapters}) 
    return arcs 

def should_skip(url:str) -> str | None: 
    lower = url.lower() 
    if lower.endswith(SKIP_SUFFIXES): 
        return "PDF link (not plain-text scrapable)" 
    domain = urlparse(url).netloc  
    if any(d in domain for d in SKIP_DOMAINS): 
        return "External file host (Mega, ect.)" 
    return None  

def extract_chapter_text(url:str): 
    try: 
        resp = requests.get(url, headers=REQUES_HEADERS, timeout= 20) 
        resp.raise_for_status()
    except Exception as e: 
        return None, f"Fetch failures: {e}" 
    soup = BeautifulSoup(resp.text,"html.parser") 
    container = None 
    for tag, attrs in CONTENT_SELECTORS: 
        container=soup.find(tag,attrs) if attrs else soup.find(tag)
        if container: 
            break 
    if container is None: 
        return None, "No recognizable content container found" 
    for junk in container.find_all(["script","style","nav","aside","form"]): 
        junk.decompose() 
    for junk in container.find_all(class_=re.compile(r"(share|related|comment|nav|widget|sidebar)",re.I)): 
        junk.decompose() 
    paragraphs = container.find_all("p") 
    text = "\n\n".join(
        p.get_text(" ", strip =True)
        for p in paragraphs
        if p.get_text(strip=True)
    ) 

    if not text: 
        return None, "Content container found but no paragraph text extracted"  
    return text, None

def scrape_arc(arc: dict, out_dir: str): 
    fname = f"Arc {arc['arc_num']:02d} - {sanatize_filename(arc['title'])}.txt" 
    fpath = os.path.join(out_dir, fname) 
    print(f"\n=== Arc {arc['arc_num']}: {arc['title']} ({len(arc['chapters'])} chapters) ===")
    with open(fpath, "w", encoding="utf-8") as f: 
        f.write(f"Arc {arc['arc_num']} - {arc['title']}\n") 
        f.write("=" * 60 + "\n\n") 

        for chap_title, chap_url in arc["chapters"]: 
            skip_reason = should_skip(chap_url) 
            if(skip_reason): 
                print(f" [SKIP] {chap_title} -> {skip_reason}")
                f.write(f"\n--- {chap_title} ---\n[SKIPPED: {skip_reason}. Source:{chap_url}]\n")
                continue 
            print(f" [FETCH] {chap_title}") 
            text,err = extract_chapter_text(chap_url) 
            f.write(f"\n--- {chap_title} ---\n\n") 
            if err: 
                print(f"    -> ERROR: {err}") 
                f.write(f"[ERROR extracting content: {err}. Source: {chap_url}]\n") 
            else: 
                f.write(text + "\n") 

            time.sleep(REQUEST_DELAY_SECONDS) 
    print(f" saved -> {fpath}") 

def main(): 
    parser = argparse.ArgumentParser(description="Scrape witch Cult Translations arcs into text files") 
    parser.add_argument("--arc",type=int, nargs="+",help = "Only scrape these arc numbers, e.g. --arc 1 3 ") 
    parser.add_argument("--list", action="store_true", help="Only print the plan, don't fetch chapters") 
    args = parser.parse_args() 
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Fetching table of contents...") 
    arcs =get_arc_plan() 
    if args.arc: 
        arcs= [a for a in arcs if a["arc_num"] in args.arc] 
    for arc in arcs: 
        print(f"Arc {arc['arc_num']}: {arc['title']} -- {len(arc['chapters'])} chapters") 
    if args.list: 
        return 
    for arc in arcs: 
        scrape_arc(arc, OUTPUT_DIR) 
    print("\nDone.") 


if __name__ == "__main__": 
    sys.exit(main())
"""""

#Translates the table of contents url into raw html code 
contents_unicode = requests.get(START_URL) 
contents_html = BeautifulSoup(contents_unicode.text, 'html.parser')
#print(contents_html.prettify()[400:1100])

#focusses on the text within the specifiend entry content divider
contents_div= content_div = contents_html.find('div', class_='entry-content')

#print(contents_div.prettify()[:900]) 

headers = contents_div.find_all("h1")

print(headers)



#Arc_name = ""
#OUTPUT_FILE = os.path.join(os.path.dirname(__file__), Arc_name)

"""
