#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import glob
import time
import re
import json
import argparse
import logging
import requests
from BeautifulSoup import BeautifulSoup


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
loghandler = logging.StreamHandler(sys.stderr)
loghandler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
log.addHandler(loghandler)

base_url = "http://www.tripadvisor.com/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"



def get_city_page(city, state, datadir):
    """ Returns the URL of the list of the hotels in a city. Corresponds to
    STEP 1 & 2 of the slides.

    Parameters
    ----------
    city : str

    state : str

    datadir : str


    Returns
    -------
    url : str
        The relative link to the website with the hotels list.

    """
    # Build the request URL
    url = base_url + "city=" + city + "&state=" + state
    # Request the HTML page
    headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    with open(os.path.join(datadir, city + '-tourism-page.html'), "w") as h:
        h.write(html)

    # Use BeautifulSoup to extract the url for the list of hotels in
    # the city and state we are interested in.

    # For example in this case we need to get the following href
    # <li class="hotels twoLines">
    # <a href="/Hotels-g60745-Boston_Massachusetts-Hotels.html" data-trk="hotels_nav">...</a>
    soup = BeautifulSoup(html)
    li = soup.find("li", {"class": "hotels twoLines"})
    city_url = li.find('a', href=True)
    return city_url['href']


def get_hotellist_page(city_url, page_count, city, datadir='data/pages'):
    """ Returns the hotel list HTML. The URL of the list is the result of
    get_city_page(). Also, saves a copy of the HTML to the disk. Corresponds to
    STEP 3 of the slides.

    Parameters
    ----------
    city_url : str
        The relative URL of the hotels in the city we are interested in.
    page_count : int
        The page that we want to fetch. Used for keeping track of our progress.
    city : str
        The name of the city that we are interested in.
    datadir : str, default is 'data/'
        The directory in which to save the downloaded html.

    Returns
    -------
    html : str
        The HTML of the page with the list of the hotels.
    """
    url = base_url + city_url
    # Sleep 2 sec before starting a new http request
    time.sleep(2)
    # Request page
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    # Save the webpage
    with open(os.path.join(datadir, city + '-hotellist-' + str(page_count) + '.html'), "w") as h:
        h.write(html)
    return html


def parse_hotellist_page(html):
    """Parses the website with the hotel list and prints the hotel name, the
    number of stars and the number of reviews it has. If there is a next page
    in the hotel list, it returns a list to that page. Otherwise, it exits the
    script. Corresponds to STEP 4 of the slides.

    Parameters
    ----------
    html : str
        The HTML of the website with the hotel list.

    Returns
    -------
    URL : str
        If there is a next page, return a relative link to this page.
        Otherwise, exit the script.
    """
    soup = BeautifulSoup(html)
    # Extract hotel name, star rating and number of reviews
    hotel_boxes = soup.findAll('div', {'class' :'listing wrap reasoning_v5_wrap jfy_listing p13n_imperfect'})
    if not hotel_boxes:
        log.info("#################################### Option 2 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing_info jfy'})
    if not hotel_boxes:
        log.info("#################################### Option 3 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing easyClear  p13n_imperfect'})

    for hotel_box in hotel_boxes:
        hotel_name = hotel_box.find("a", {"target" : "_blank"}).find(text=True)
        log.info("Hotel name: %s" % hotel_name.strip())

        stars = hotel_box.find("img", {"class" : "sprite-ratings"})
        if stars:
            log.info("Stars: %s" % stars['alt'].split()[0])

        num_reviews = hotel_box.find("span", {'class': "more"}).findAll(text=True)
        if num_reviews:
            log.info("Number of reviews: %s " % [x for x in num_reviews if "review" in x][0].strip())

    # Find the next page.
    #
    # Use regular expression because for some reason it won't
    # find a basic string.
    nextPage = soup.find("a", {'class': re.compile(r'\bsprite-pageNext\b')})
    if nextPage:
        return nextPage["href"]
    else:
        print "We reached last page"

# Return a list of all hotels and their url
def get_list_of_hotels(path = 'data/pages'):
    # Combine all hotel pages into one
    html = ""
    for file in glob.glob(os.path.join(path, '*.html')):
        with open(file, 'r') as page:
            html = html + page.read()

    # Find each hotel
    soup = BeautifulSoup(html)
    hotels = soup.findAll('div', {'class' :'listing wrap reasoning_v5_wrap jfy_listing p13n_imperfect'})

    # Extract each hotel's id and url
    hotel_list = []
    for hotel in hotels:
        title = hotel.find("a", {'class': 'property_title'})
        url = title["href"]
        property_id = title["id"]
        hotel_list.append({
            'id': property_id,
            'url': url
        })

    return hotel_list

def get_hotel_page(url, saveAs = None):
    url = base_url + url
    # Sleep 2 sec before starting a new http request
    time.sleep(2)
    # Request page
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')

    # Save the webpage
    if saveAs:
        with open(os.path.join(datadir, city + '-hotel-' + str(saveAs) + '.html'), "w") as h:
            h.write(html)

    return html

def get_hotel_info(url):
    html = get_hotel_page(url)
    soup = BeautifulSoup(html)

    details = soup.find(id="REVIEWS")

    # number of reviews this place has
    reviews = int(re.sub(r"\D", "", details.find('h3', {'class': 'reviews_header'}).text))

    # how many ratings of each type
    ratings = {}
    for rating in details.find('ul', {'class': 'barChart'}).findAll('div', {'class': 'wrap row'}):
        rType = rating.find('span', {'class': 'text'}).text
        rAmount = rating.find('span', {'class': 'compositeCount'}).text

        ratings[rType] = int(re.sub(r"\D", "", rAmount))

    # how many reviews for each trip type
    tripType = {}
    for review in details.find('div', {'class': 'trip_type'}).findAll('div', {'class': re.compile(r'\bsegment\b')}):
        rType = review.find('div', {'class': re.compile(r'\bfilter_selection\b')}).text
        rAmount = review.find('div', {'class': 'value'}).text

        tripType[rType] = int(re.sub(r"\D", "", rAmount))

    # rating of each attribute
    summary = {}
    for attr in details.find(id="SUMMARYBOX").findAll('li'):
        name = attr.find('div', {'class': 'name'}).text
        rating = attr.find('span', {'class': 'rate sprite-rating_s rating_s'}).find('img')['alt']

        summary[name] = float(rating.split(' ')[0])

    return {
        'reviews': reviews,
        'ratings': ratings,
        'tripType': tripType,
        'summary': summary
    }

def save_info_of_hotel_list(output_file = 'data/hotel-info.json'):
    hotels = get_list_of_hotels()

    i = 1
    info = []
    for hotel in hotels:
        print '{} of {} hotels.\n'.format(i, len(hotels))
        info.append(get_hotel_info(hotel['url']))
        i += 1

    # Encode as json for writing to new file
    encoded = json.dumps(info)

    # Write to new file
    with open(output_file, "w") as output:
        output.write(encoded)

def scrape_hotels(city, state, datadir='data/'):
    """Runs the main scraper code

    Parameters
    ----------
    city : str
        The name of the city for which to scrape hotels.

    state : str
        The state in which the city is located.

    datadir : str, default is 'data/'
        The directory under which to save the downloaded html.
    """

    # Get current directory
    current_dir = os.getcwd()
    # Create datadir if does not exist
    if not os.path.exists(os.path.join(current_dir, datadir)):
        os.makedirs(os.path.join(current_dir, datadir))

    # Get URL to obtaint the list of hotels in a specific city
    city_url = get_city_page(city, state, datadir)
    c = 0
    while(city_url):
        c += 1
        print (c, city_url)
        html = get_hotellist_page(city_url, c, city, datadir + "pages")
        city_url = parse_hotellist_page(html)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape tripadvisor')
    parser.add_argument('-datadir', type=str,
                        help='Directory to store raw html files',
                        default="data/")
    parser.add_argument('-state', type=str,
                        help='State for which the hotel data is required.',
                        required=True)
    parser.add_argument('-city', type=str,
                        help='City for which the hotel data is required.',
                        required=True)

    args = parser.parse_args()
    scrape_hotels(args.city, args.state, args.datadir)
