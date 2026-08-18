import requests
from bs4 import BeautifulSoup
import time
import re
import os
#START_URL = "https://witchculttranslation.com/2021/05/19/arc-1-chapter-1-ususable-ridged-10/"
START_URL = "https://witchculttranslation.com/2021/05/19/prologue-waste-heat-of-the-beginning/"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "rezero_web_novel.txt")

def get_chapter(url):
    response = requests.get(url) #gets unicode values 
    soup = BeautifulSoup(response.text, 'html.parser') #translatess unicode into html
    

    # Get chapter title
    title = soup.find('h1') #searches through html for the title heading
    title_text = title.get_text(strip=True) if title else "Unknown Chapter"
    
    # Get chapter content div
    content_div = soup.find('div', class_='entry-content')
    if not content_div:
        return None, None, None
    
    # Get all paragraphs or <p> code from html
    paragraphs = content_div.find_all('p')
    

    clean_paragraphs = []
    novel_started = False
    separator_count = 0
    
    for p in paragraphs:
        text = p.get_text(strip=True)
        
        # Skip empty paragraphs
        if not text:
            continue
        
        # Count separator lines
        if '※' in text:
            separator_count += 1
            # Novel text starts after the 3rd separator
            if separator_count >= 3:
                novel_started = True
            continue
        
        # Skip translator credits and rights notice
        if any(skip in text for skip in [
            'Translated By',
            'ALL RIGHTS BELONG',
            'JAPANESE WEB NOVEL SOURCE',
            'Translation By',
            'Translated by'
        ]):
            continue
            
        # Skip navigation text
        if any(skip in text for skip in [
            'Previous Post',
            'Next Post',
            'Posted in',
            'Posted on'
        ]):
            continue
        
        # Only include actual novel content
        if novel_started and text:
            clean_paragraphs.append(text)
    
    novel_text = '\n\n'.join(clean_paragraphs)
    
    # Get next chapter link
    next_link = soup.find('a', rel='Next Post')
    next_url = next_link['href'] if next_link else None
    
    return title_text, novel_text, next_url

# Start scraping  
chapter_count = 0

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    url = START_URL
    chapter_count = 0
    
    while url:
        print(f"Scraping chapter {chapter_count + 1}: {url}")
        title, text, next_url = get_chapter(url)
        
        if not text:
            print(f"Could not get content, stopping.")
            break
        
        f.write(f"\n\n{'='*60}\n")
        f.write(f"{title}\n")
        f.write(f"{'='*60}\n\n")
        f.write(text)
        f.flush()  # Save progress as we go
        
        chapter_count += 1
        print(f"✓ Got: {title}")
        
        url = next_url
        time.sleep(1) 


print(f"\nDone! Scraped {chapter_count} chapters to {OUTPUT_FILE}") 