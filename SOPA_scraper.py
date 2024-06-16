import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "https://bo.um.warszawa.pl"
PROJECTS_LIST_URL = BASE_URL + "/projects?page={page_number}"

def get_page_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to retrieve page {page_number}. Status code: {response.status_code}")
        return None


def parse_page_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # You can customize the parsing logic based on the structure of the webpage
    return soup

def get_projects_list_grid(soup):
    projects_list_grid = soup.find('tbody', attrs={"id": "projects-list"})
    return projects_list_grid

def extract_project_links(projects_list_grid):
    project_links = []
    rows = projects_list_grid.find_all('tr')
    for row in rows:
        title_column = row.find('td', class_='text-left title-column')
        if title_column:
            link = title_column.find('a')
            if link:
                project_links.append(link['href'])
    return project_links

def get_full_urls(project_links, base_url):
    full_urls = [base_url + link for link in project_links]
    return full_urls

def get_project_info(soup, strong_text):
    strong_tag = soup.find('strong', string=strong_text)
    if strong_tag:
        next_tag = strong_tag.find_next_sibling()
        if next_tag:
            return next_tag.text.strip()
    return None

def get_all_subsequent_paragraphs(soup, strong_text):
    strong_tag = soup.find('strong', string=strong_text)
    paragraphs = []
    if strong_tag:
        next_sibling = strong_tag.find_next_sibling()
        while next_sibling and next_sibling.name == 'p':
            paragraphs.append(next_sibling.text.strip())
            next_sibling = next_sibling.find_next_sibling()
    return paragraphs

def get_list_elements(soup, strong_text):
    strong_tag = soup.find('strong', string=strong_text)
    html_list = strong_tag.find_next_sibling()
    res = []
    if html_list.name == 'ul':
        for el in html_list:
            text = el.text.strip()
            if text:
                res.append(text)
    return res

def get_text_after_strong_tag(soup, strong_text):
    strong_tag = soup.find('strong', string=strong_text)
    if strong_tag:
        next_element = strong_tag.next_sibling
        while next_element and next_element.name is None:
            text = next_element.strip()
            if text:
                return text
            next_element = next_element.next_sibling
    return None



if __name__ == "__main__":
    scraped_data = []

    page_number = 1
    project_list_html_content = get_page_content(PROJECTS_LIST_URL.format(page_number=page_number))
    while project_list_html_content:
        print(f"Processing project list #{page_number}")
        project_list_parsed_content = parse_page_content(project_list_html_content)
        projects_list_grid = get_projects_list_grid(project_list_parsed_content)
        project_url_sufix = extract_project_links(projects_list_grid)
        project_full_urls = get_full_urls(project_url_sufix, BASE_URL)
        for project_full_url in project_full_urls:
            print(" |", end='')
            project_page_html = get_page_content(project_full_url)
            project_page_content = parse_page_content(project_page_html)
            proj_ = {
                "localization": get_project_info(project_page_content, 'Lokalizacja projektu - ulica i nr / rejon ulic w Warszawie:'),
                "short_desc": get_project_info(project_page_content, "Skrócony opis projektu:"),
                "long_desc": get_all_subsequent_paragraphs(project_page_content, "Opis projektu:"),
                "categories": get_list_elements(project_page_content, "Kategoria tematyczna projektu:"),
                "beneficiaries": get_list_elements(project_page_content, "Potencjalni odbiorcy projektu:"),
                "est_cost": get_text_after_strong_tag(project_page_content, "Szacunkowy koszt realizacji projektu:"),
            }
            scraped_data.append(proj_)
        print()
        page_number += 1
        if page_number > 10:
            break
        project_list_html_content = get_page_content(PROJECTS_LIST_URL.format(page_number=page_number))

    print(f"Total projects scraped: {len(scraped_data)}")

    file_path = "scraped_data.json"
    with open(file_path, 'w') as json_file:
        json.dump(scraped_data, json_file, indent=4)
