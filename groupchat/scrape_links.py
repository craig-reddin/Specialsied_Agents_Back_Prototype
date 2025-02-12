# filename: scrape_links.py

import requests
from bs4 import BeautifulSoup

def scrape_links(url):
    # Fetch the content of the webpage
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all anchor tags and extract the href attributes
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        
        # Print the extracted links
        for link in links:
            print(link)
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

# URL of the webpage to scrape
url = "https://www.python.org"

# Call the function to scrape links
scrape_links(url)