import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin # This helps combine base_url + /verdzi
import time # To be polite to the server
import os

# Configuration
WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")
TARGET_URL = "https://horoskopi.ge"

name_sign_map = {
    "ვერძი": "♈",
    "კურო": "♉",
    "ტყუპები": "♊",
    "კირჩხიბი": "♋",
    "ლომი": "♌",
    "ქალწული": "♍",
    "სასწორი": "♎",
    "მორიელი": "♏",
    "მშვილდოსანი": "♐",
    "თხის რქა": "♑",
    "მერწყული": "♒",
    "თევზები": "♓"
}

def get_zodiac_links():
    response = requests.get(TARGET_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    zodiac_map = {}

    # 1. Find all div elements with the class 'horoscope_box'
    boxes = soup.find_all('div', class_='horoscope_box')

    for box in boxes:
        # 2. Find the <a> tag inside the box
        link_tag = box.find('a')
        if link_tag and link_tag.get('href'):
            # 3. Get the text (e.g., 'Verdzi') and the full URL
            # We use urljoin in case the link is just '/verdzi'
            relative_url = link_tag.get('href')
            full_url = urljoin(TARGET_URL, relative_url)
            
            # 4. Get the name of the sign (cleaning up whitespace)
            span_tag = link_tag.find('span')
            name = span_tag.get_text(strip=True)
            sign = name_sign_map[name]
            name = sign + " " + name
            
            zodiac_map[name] = full_url

    return zodiac_map

def get_zodiac_details():
    final_data = {}
    zodiac_map = get_zodiac_links()
    
    for name, url in zodiac_map.items():
        print(f"Scraping details for: {name}...")
        
        try:
            # 1. Visit the specific zodiac page
            response = requests.get(url)
            response.encoding = 'utf-8' # Crucial for Georgian characters
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 2. Find the detail text. 
            # Based on your previous image, we look for the main text block.
            # Replace 'horoscope_text_class' with the actual class you see in Inspect
            detail_div = soup.find('div', class_='full_descr') 
            
            if detail_div:
                # Get the text and clean it up
                text = detail_div.get_text(strip=True)
                # Keep only the first 4-5 sentences as requested
                sentences = text.split('.')[:5]
                clean_text = ".".join(sentences) + "."
                final_data[name] = clean_text
            else:
                final_data[name] = "Information not found."
            
            # 3. Wait a tiny bit so the site doesn't think you're a bot
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"Error scraping {name}: {e}")
            final_data[name] = "Error retrieving data."

    return final_data

def send_to_teams(data):
    facts = []
    for sign, text in data.items():
        facts.append({"title": sign, "value": text})

    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "✨ Daily Zodiac Insights",
                            "weight": "Bolder",
                            "size": "ExtraLarge",
                            "color": "Accent"
                        },
                        {
                            "type": "FactSet",
                            "facts": facts,
                            "separator": True
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "View Full Website",
                            "url": "https://horoskopi.ge"
                        }
                    ],
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json"
                }
            }
        ]
    }
    
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    send_to_teams(get_zodiac_details())