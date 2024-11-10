import bs4
import csv
import logging
import requests

# Главный URL
main_url = 'https://yacht-parts.ru/'
FILENAME = 'yacht-parts-ru.csv'
out_data = []
logging.basicConfig(level=logging.INFO,
                    filename='yacht-parts-ru_parsing_log.log',
                    filemode='w',
                    format='%(asctime)s %(levelname)s %(message)s')


# Функция для получения soup-ответа
def get_soup(url):
    while True:
        try:
            res = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                              'AppleWebKit/537.36 (KHTML, like Gecko)'
                              'Chrome/130.0.0.0 Safari/537.36'})
            break
        except requests.ConnectionError:
            logging.exception('Не удалось подключиться к серверу')
    return bs4.BeautifulSoup(res.text, 'html.parser')


# Получение страницы всех категорий товаров
catalog_page = get_soup(main_url + '/catalog/')
logging.info("Подключение установлено.")
# Поиск всех <ul> с классом 'subsections'
categories_list = catalog_page.find_all('ul', class_='subsections')

# Список всех категорий
categories = []

# Прохождение по найденным <ul>, т.е. категориям товаров
for ul in categories_list:
    # Поиск всех <li> с классом 'sect'
    lis = ul.find_all('li', class_='sect')

    # Прохождение по найденным <li>
    for li in lis:
        # Извлечение тега <a>
        tag_a = li.find('a')
        # Получение текста и ссылки из <a> и href соответственно, при
        # условии, что тег <a> существует
        if tag_a:
            text = tag_a.text.strip()
            href = tag_a['href'].strip()
            categories.append(
                {'category': text,
                 'href': href
                 }
            )

# Перебор каждой категории товаров
iter = 1
logging.info(f'Все категории ({len(categories)}) успешно сформированы.')
for cat in categories:
    logging.info(f"Перебор {iter}-й категории, категория: {cat['category']}")

    # Получение всех товаров на странице
    product_page = get_soup(main_url + cat['href'])
    # Узнаём количество страниц, путём нахождения
    # всех тегов <a> внутри <span class='nums'"'>
    links_span_exist = product_page.find('span', class_='nums')
    pages_count = 1
    if links_span_exist:
        links_span = links_span_exist.find_all('a')
        pages_count = int(links_span[-1].get_text())

    # Прохождение по всем страницам одной категории (Якоря, кранцы и т.д.)
    for page in range(1, pages_count + 1):
        product_page = get_soup(main_url + cat['href'] + f'?PAGEN_1={page}')
        products_list = product_page.find_all(
            'div', class_='list_item_wrapp item_wrap')

        # Перебор каждого товара
        for product in products_list:
            tag_a = product.find('a')
            href = tag_a['href'].strip()
            product_page = get_soup(main_url + href)

            """
            Тег <a> используется только тогда, когда у товара есть бренд
            В противном случае, тега <a> не существует вовсе
            Если тега <a> не существует, то вместо бренда будет символ '—'
            """

            # Получение наименования товара, если он существует
            product_name_exist = product_page.find('h1')
            product_name = product_name_exist.get_text().strip() if product_name_exist else '—'

            # Получение артикула, если он существует
            product_article_exist = product_page.find('span', class_='value')
            product_article = product_article_exist.get_text().strip() if product_article_exist else '—'

            # Получение бренда, если он существует
            product_brand_exist = product_page.find(
                'a', class_='brand_picture')
            product_brand_img = product_brand_exist.find(
                'img') if product_brand_exist else None
            product_brand = (product_brand_img.get(
                'title', '—')) if product_brand_img else '—'

            # Получение цены товара, если она существует
            product_price_exist = product_page.find(
                'div', class_='price')
            product_price = product_price_exist.get_text().strip() if product_price_exist else '—'

            # Получение описания товара, если оно существует
            product_desc_exist = product_page.find(
                'div', class_='preview_text')
            product_desc = product_desc_exist.get_text() if product_desc_exist else '—'

            # Получение ссылок на изображения товара
            # Список ссылок на изображения
            product_links_images = []
            # Список тегов <a>
            product_images_exist = product_page.find(
                'div', class_='item_slider')
            product_images = product_images_exist.find_all(
                'a') if product_images_exist else '—'
            for image in product_images:
                if image != '—':
                    product_links_images.append(image['href'].strip())

            try:
                out_data.append([
                    cat['category'],
                    product_article,
                    product_brand,
                    product_name,
                    product_price,
                    product_desc,
                    product_links_images
                ])
            except TypeError:
                logging.exception(
                    f"Не удалось записать данные о товаре '{product_name}' в список")

logging.info('Идёт операция записи строк в csv файл.')
with open(FILENAME, 'w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file, delimiter=';')
    try:
        writer.writerow(
            ['Категория', 'Артикул', 'Бренд', 'Наименование товара', 'Цена',
             'Описание', 'Ссылки на изображения'])
    except IOError:
        logging.exception('Произошла ошибка при создании названия колонок')
    for data in out_data:
        try:
            writer.writerow(data)
        except IOError:
            logging.exception(
                f'Произошла ошибка при записи в файл следующей информации: {data}')
logging.info('Запись в csv файл окончена.')