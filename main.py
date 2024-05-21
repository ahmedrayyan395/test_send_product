import json
import requests
from bs4 import BeautifulSoup
import time
import re

# Global list to store product names that are successfully sent
sent_products = []

# Variable to store the time of the last clearing of the sent_products list
last_clear_time = time.time()

# Function to fetch URL content with retries
def fetch_url_with_retry(url, max_retries=7, delay=1):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.content
            else:
                print(f"Failed to fetch URL: {url}. Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
        retries += 1
        time.sleep(delay)
    print(f"Max retries reached for URL: {url}")
    return None

# Function to extract product details and image URL
def extract_product_details(product_url):
    try:
        response = requests.get(product_url)
        html_content = response.content
        soup = BeautifulSoup(html_content, "html.parser")

        product_name = soup.find("span", class_="base", itemprop="name").text.strip()
        product_status_element = soup.find("div", class_="stock unavailable").span
        product_status = product_status_element.text.strip() if product_status_element else None

        
      # Extract all image URLs and find the one containing the desired pattern
       # Extract all image URLs and find the one containing the desired pattern
        images = soup.find_all("img")
        pattern = "https://assets.dzrt.com/media/catalog/product/cache/bd08de51ffb7051e85ef6e224cd8b890/"
        image_url = None
        for img in images:
            src = img.get('data-src') or img.get('src')
            if src and pattern in src:
                image_url = src
                break




        return product_name, product_status, image_url
    except Exception as e:
        print(f"still not available  for {product_url}: {str(e)}")
        return None, None, None

# Function to send product data to Telegram
def send_product_data_to_telegram():
    global sent_products, last_clear_time

    url = "https://www.dzrt.com/ar/our-products.html"
    html_content = fetch_url_with_retry(url)
    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        product_links = [a["href"] for a in soup.find_all("a", class_="product-item-link")]

        product_data_list = []
        for product_link in product_links:
            product_info = {"url": product_link}
            product_name, product_status, image_url = extract_product_details(product_link)
            if product_name and product_status:
                product_info.update({"name": product_name, "status": product_status, "image_url": image_url})
                product_data_list.append(product_info)
                print(f"Product Name: {product_name}")
                print(f"Product Status: {product_status}")
                print(f"Image URL: {image_url}")
                print("-" * 50)

        bot_token = "6958486146:AAFtYb_TaInJtSSFevXDn39BCssCzj4inV4"
        chat_id = "@desertfs"
        telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

        for product_data in product_data_list:
            product_name = product_data.get("name", "")
            product_status = product_data.get("status", "")
            product_url = product_data.get("url", "")
            image_url = product_data.get("image_url", "")

            if product_status == "سيتم توفيرها في المخزون قريباً" and product_name not in sent_products:
                message_text = f"Product Name: {product_name}\nProduct Status: {product_status}"
                reply_markup = {
                    "inline_keyboard": [[{"text": "View Product", "url": product_url}]]
                }
                params = {
                    "chat_id": chat_id,
                    "photo": image_url,
                    "caption": message_text,
                    "reply_markup": json.dumps(reply_markup)
                }
                response = requests.post(telegram_api_url, params=params)

                if response.status_code == 200:
                    print(f"Product data sent successfully for {product_name}")
                    sent_products.append(product_name)
                else:
                    print(f"Failed to send product data for {product_name}. Status code: {response.status_code}")

        if time.time() - last_clear_time >= 60:
            sent_products.clear()
            last_clear_time = time.time()

# Main loop to run the code every minute
while True:
    send_product_data_to_telegram()
   # time.sleep(20)
