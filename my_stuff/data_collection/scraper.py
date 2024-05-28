import datetime
import csv
import requests
from bs4 import BeautifulSoup
import time
import random

'''
Data Format:
- 2 equal sized sets (trg, tst).csv
- Each line: 
id,class,abstract

The data will be news data.  The class will indicate whether the NASDAQ went up or down on that day (data from the Nasdaq Composite Index IXIC).  The abstract will be an unbiased summary of the news article. 
Classes will be 'U' and 'D' for up and down respectively.

'''
class News:
    def __init__(self, id: int, date_: datetime.datetime, class_: str | None = None, abstract: str = "") -> None:
        self.id: int = id
        self.date_: datetime.datetime = date_
        self.class_: str | None = class_
        self.abstract: str = abstract


def get_stock_data() -> dict[datetime.datetime, str]:
    '''Pulls the Yahoo finance data.'''
    with open(r'data_collection/IXIC.csv', 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
    stock_data = {}
    for i in range(1, len(data)):
        stock_data[datetime.datetime.strptime(data[i][0], '%Y-%m-%d')] = data[i][4]
    stock_class = {}
    prev_keys = list(stock_data.keys())
    for i in range(1, len(stock_data)):
        if float(stock_data[prev_keys[i]]) > float(stock_data[prev_keys[i - 1]]):
            stock_class[prev_keys[i]] = 'U'
        else:
            stock_class[prev_keys[i]] = 'D'
    return stock_class # this is now a dict with the date as the key and the class as the value (U or D)


def add_class_to_news(news: list[News], stock_data: dict[datetime.datetime, str]) -> list[News]:
    for n in news:
        if not n.date_ is None:
            for date_, class_ in stock_data.items():
                if date_.year == n.date_.year and date_.month == n.date_.month and date_.day == n.date_.day:
                    n.class_ = class_
                    break
    return news


def datetime_handle(date_string: str, year: int) -> datetime.datetime:
    '''
    Handles for 4 different scenarios/formats:
    1. Month day (ideal)
    2. Month (take the first day of the month)
    3. Month day – Month day (takes the first date)
    4. Other (don't throw an error, just return None)
    '''
    try:
        date_ = datetime.datetime.strptime(date_string, '%B %d')
        date_ = date_.replace(year=year)
    except ValueError:
        try:
            date_ = datetime.datetime.strptime(date_string, '%B')
            date_ = date_.replace(year=year, day=1)
        except ValueError:
            try:
                date_ = datetime.datetime.strptime(date_string.split('–')[0].strip(), '%B %d')
                date_ = date_.replace(year=year)
            except ValueError:
                try:
                    date_ = datetime.datetime.strptime(date_string.split('–')[0].strip(), '%B')
                    date_ = date_.replace(year=year, day=1)
                except ValueError:
                    print(f"Cannot parse date: {date_string}")
                    return None
    return date_


def get_articals_year_page(url: str, year: int, starting_id: int = 0) -> list[News]:
    html_text = requests.get(url).text
    '''
    get everything between Events and either:
    - date unknown (if it exists) [id="Date_unknown"]
    - onggoing (if it exists) [id="Ongoing"]
    If neither, Births [id="Births"]
    '''

    events_index = html_text.index('id="Events"')
    html_text = html_text[events_index:]
    if 'id="Date_unknown"' in html_text:
        date_unknown_index = html_text.index('id="Date_unknown"')
        html_text = html_text[:date_unknown_index]
    elif 'id="Ongoing"' in html_text:
        ongoing_index = html_text.index('id="Ongoing"')
        html_text = html_text[:ongoing_index]
    elif 'id="Births"' in html_text:
        births_index = html_text.index('id="Births"')
        html_text = html_text[:births_index]
    else:
        deaths_index = html_text.index('id="Deaths"')
        html_text = html_text[:deaths_index]

    bs: BeautifulSoup = BeautifulSoup(html_text, 'html.parser')
    '''
    There are two cases for the structure of a news article in the html:
        1. In the first case, the date is in the save <li> as the abstract as there is only one artical for that day
            a. In this case, we can get the date by getting all the text. Text.split('-')[0] will give us the date, and [1] the abstract.
        2. In the second, there are multiple articals for that day. Then we have the date in an outer <li>, and a separate <ul> inside with each artical.
            a. In this case, we get the date from the outer <li> and apply it to each of the abstracts in the children
    We will need to handle both cases.
    '''
    news: list[News] = [] 
    previous_lines: list[str] = []
    just_date_value: datetime.datetime = None
    for li in bs.find_all('li'):
        all_text = ''.join([t for t in li.find_all(text=True)])
        if all_text.count('\n') > 1:
            lines_ = all_text.split('\n')
            if not any(l in previous_lines for l in lines_):
                date_ = datetime_handle(lines_[0].strip(), year)
                for i in range(1, len(lines_)):
                    if lines_[i] != '':
                        if date_ is not None:
                            news.append(News(id=starting_id, date_=date_, abstract=lines_[i]))
                            starting_id += 1
                previous_lines = lines_
        else:
            if not all_text in previous_lines:
                date_parse_test = datetime_handle(all_text.strip(), year)
                if date_parse_test is not None and len(all_text.split('–')) == 1:
                    just_date_value = date_parse_test
                else:
                    if len(all_text.split('–')) == 1:
                        date_ = just_date_value
                        abstract_ = all_text
                        if date_ is not None:
                            news.append(News(id=starting_id, date_=date_, abstract=abstract_))
                            starting_id += 1
                    else:
                        date_ = datetime_handle(all_text.split('–')[0].strip(), year)
                        if date_ is not None:
                            abstract_ = all_text.split('–')[1].strip()
                            news.append(News(id=starting_id, date_=date_, abstract=abstract_))
                            starting_id += 1
    return news 


def just_get_year_page(stock_data) -> list[News]:
    start_year = 1971
    total_news: list[News] = []
    for year in range(start_year, 2025):
        print(f'Getting {year} data')
        try:
            news = get_articals_year_page(f'https://en.wikipedia.org/wiki/{year}_in_the_United_States', year)
            news = add_class_to_news(news, stock_data)
            print(f'Got {len(news)} articles for {year}')
            total_news += news
        except Exception as e:
            print(f'Failed to get {year} data')
            print(e)
            print(e.__traceback__.tb_lineno)
    with open('data_collection/news.csv', 'w', encoding='utf-8') as f:
        f.write('id,class,abstract\n')
        for n in total_news:
            f.write(f'{n.id},{n.class_},{n.abstract}\n')


def clean_data(input_csv: str) -> None:
    cur_id = 0
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        data = list(reader)
    news = []
    for i in range(1, len(data)):
        if len(data[i]) < 3:
            print(f"{i}: {data[i]}")
        else:
            if data[i][1] != "None" and len(data[i][2]) > 5:
                cur_abstract = data[i][2]
                while '[' in cur_abstract:
                    start = cur_abstract.index('[')
                    end = cur_abstract.index(']')
                    cur_abstract = cur_abstract[:start] + cur_abstract[end + 1:]
                news.append(News(id=cur_id, date_=None, class_=data[i][1], abstract=cur_abstract))
                cur_id += 1
    new_id = 0
    with open('data_collection/news_cleaned.csv', 'w', encoding='utf-8') as f:
        f.write('id,class,abstract\n')
        for n in news:
            f.write(f'{n.id},{n.class_},{n.abstract}\n')


def get_articals_portal_page(url: str, year: int, month: str) -> list[News]:
    return []


def get_wikipedia_news() -> list[News]:
    '''
    This will get all of the news articals from the two wikipedia pages.
    
    1. https://en.wikipedia.org/wiki/Portal:Current_events/{month}_{year}
    - This has news articles for each day of the month with international events

    2. en.wikipedia.org/wiki/{year}_in_the_United_States 
    - This has news articles for each day of the year with US events

    Sometimes news will be duplicated, ie, on both pages. 
    This is fine as it helps bias the model towards the US, and the NASDAQ data is also US based.
    
    Each of the two pages will require a different html parser as the structure is different.
    To ensure that we don't have requests failing we will use a try except block and have sleep times between requests.
    '''
    base_url: str = 'https://en.wikipedia.org/wiki/'
    starting_year: int = 1971
    current_year: int = datetime.datetime.now().year
    news: list[News] = []
    for year in range(starting_year, current_year + 1):
        news += get_articals_year_page(f'{base_url}{year}_in_the_United_States', year)

        for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']:
            if not (year == starting_year and month == 'January'):
                news += get_articals_portal_page(f'{base_url}Portal:Current_events/{month}_{year}', year, month)
    return news


if __name__ == '__main__':
    # news = get_wikipedia_news()
    # stock_data = get_stock_data()
    clean_data('data_collection/news.csv')
    with open('data_collection/news_cleaned.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        data = list(reader)
    random.shuffle(data)
    split = len(data) // 2

    with open('data_collection/tst.csv', 'w', encoding='utf-8') as f:
        f.write('id,class,abstract\n')
        for i in range(split):
            f.write(f'{data[i][0]},{data[i][1]},{data[i][2]}\n')

    with open('data_collection/trg.csv', 'w', encoding='utf-8') as f:
        f.write('id,class,abstract\n')
        for i in range(split, len(data)):
            f.write(f'{data[i][0]},{data[i][1]},{data[i][2]}\n')

