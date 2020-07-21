from imdb import IMDb
import requests
import re
import bs4 as bs4
import csv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep


def get_page_db_html(url):
    headers = {
        'Referer': 'https://movie.douban.com',
        'Host': 'movie.douban.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None


def get_page_rt_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None


def get_page_dbpic_html(url):
    headers = {
        'referer': 'https://movie.douban.com',
        'host': 'movie.douban.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        # 'accept-encoding': 'gzip, deflate, br',
        # 'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        # 'sec-fetch-dest': 'document',
        # 'sec-fetch-mode': 'navigate',
        # 'sec-fetch-site': 'none',
        # 'sec-fetch-user': '?1',
        # 'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None


def get_movie_db_info(url):
    html = get_page_db_html(url)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    content = soup.find('div', id='content')
    try:
        review = content.find('strong', property='v:average').text
        if review == '':
            review = 'n/a'
            print('douban rating not available')
    except IndexError:
        review = 'n/a'
        print('douban rating not available')
    return review


def get_movie_rt_info(url):
    html = get_page_rt_html(url)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    content = soup.find_all('span', class_='mop-ratings-wrap__percentage')
    try:
        review = content[0].text.strip()
        if review == '':
            review = 'n/a'
            print('rotten tomatoes rating not available')
    except IndexError:
        review = 'n/a'
        print('rotten tomatoes rating not available')
    return review


def get_movie_dbpic_info(url):
    html = get_page_dbpic_html(url)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    try:
        content = soup.find_all('div', class_='cover')[0]
        poster_url = content.contents[1].contents[1].attrs['src']
    except IndexError:
        print('Poster not found')
        poster_url = ''
    return poster_url


if __name__ == '__main__':
    # get information for IMDb
    ia = IMDb()
    with open('movie_data.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            number = str(row[0])

            # get movie information from IMDb
            movie = ia.search_movie(str(row[1]))
            movieid = movie[0].movieID
            movietitle = str(ia.get_movie(movieid)).replace('?', '')
            movieinfo = ia.get_movie(movieid, info=['main'])
            tags = movieinfo.get('genres')
            review = str(movieinfo.get('rating'))
            plot = str(movieinfo.get('plot outline'))
            release_year = str(movieinfo.get('year'))
            title_post = movietitle.replace(': ', ' - ')
            title_name = movietitle.replace(' ', '-').replace(':', '').replace('\'', '').replace('?', '').replace('.', '').lower()
            title_img = movietitle.replace(' ', '_').replace(':', '').replace('\'', '').replace('?', '').replace('.', '').lower()
            imdb_url = ia.get_imdbURL(movie[0])

            print(number)
            print(movietitle)

            # get movie review from douban and rotten tomatoes
            try:
                from googlesearch import search
            except ImportError:
                print("No module named 'google' found")
            query = 'douban movie ' + movietitle + release_year
            douban_url = ''
            for j in search(query, tld="com", num=10, stop=10, pause=2):
                if j.startswith('https://movie.douban.com/subject') and re.match('[0-9]+[/][/]$|[0-9]+[/]$', j[33:]):
                    douban_url = j
                    break
                elif j.startswith('https://m.douban.com/movie/subject') and re.match('[0-9]+[/][/]$|[0-9]+[/]$', j[35:]):
                    douban_url = 'https://movie.douban.com/subject/' + j[35:]
                    break
            query = 'rotten tomatoes ' + movietitle + release_year
            rotten_url = ''
            for i in search(query, tld="com", num=10, stop=10, pause=2):
                if i.startswith('https://www.rottentomatoes.com/m/'):
                    rotten_url = i
                    break
            if douban_url != '':
                douban_rating = str(get_movie_db_info(douban_url))
            else:
                douban_rating = 'n/a'
            if rotten_url != '':
                rotten_rating = str(get_movie_rt_info(rotten_url))
            else:
                rotten_rating = 'n/a'


            # get douban posters
            if douban_url != '':
                if douban_url[-2] == '/':
                    dbpic_url = douban_url[0:len(douban_url) - 1] + 'photos?type=R'
                else:
                    dbpic_url = douban_url[0:len(douban_url) - 1] + '/photos?type=R'
                poster_url = get_movie_dbpic_info(dbpic_url)
                if poster_url != '':
                    poster_url_lst = poster_url.split('.')
                    poster_url_lst[-1] = 'jpg'
                    poster_url = '.'.join(poster_url_lst)

                    # open the link of douban poster
                    driver = webdriver.Chrome(ChromeDriverManager().install())
                    driver.get(poster_url)
                    sleep(1)
                    driver.close()
                    # print(poster_url)

                    # download douban poster
                    filename = './imgs/' + title_img + '.jpg'
                    r = requests.get(poster_url, allow_redirects=True)
                    open(filename, 'wb').write(r.content)
                    # urlretrieve(poster_url, filename)

            # create markdown for movies
            with open('./posts/' + str(release_year) + '-01-01-' + title_name + '.markdown', 'w', encoding="utf-8") as f:
                f.write('---\nlayout: post \ntitle: ' + title_post + '\nimg: ' + title_img + '.jpg\ntags: [')
                for i in range(len(tags) - 1):
                    f.write(tags[i] + ', ')
                f.write(tags[-1] + ']\n')
                f.write('number: No. ' + number +'\n')
                f.write('review: [豆瓣 ' + douban_rating + ', IMDb ' + review + ', Rotten Tomatoes ' + rotten_rating + ']\n')
                # f.write('Douban '+ douban_rating + ': [' + douban_url + ']\n')
                # f.write('IMDb ' + review + ': [' + imdb_url + ']\n')
                # f.write('Rotten Tomatoes ' + rotten_rating + ': [' + rotten_url + ']\n---\n\n' + plot)
                f.write('douban_link: ' + douban_url +'\nimdb_link: ' + imdb_url + '\nrotten_link: ' + rotten_url + '\n---\n\n' + plot)

            # update movie list with addition(s)
            # with open('movie_list.csv', 'a') as m:
            #     writer = csv.writer(m, delimiter=',')
            #     writer.writerow([number, movietitle])