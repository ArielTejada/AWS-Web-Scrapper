import os
from dotenv import load_dotenv
import requests
import boto3
from bs4 import BeautifulSoup
from datetime import date, datetime
import time


def main():
    load_dotenv()

    # URL = "https://www.bestbuy.com/site/gigabyte-nvidia-geforce-rtx-4090-gaming-oc-24gb-gddr6x-pci-express-4-0-graphics-card-black/6521518.p?skuId=6521518"
    URL = "https://www.bestbuy.com/site/intel-core-i9-13900k-13th-gen-24-cores-8-p-cores-16-e-cores-36m-cache-3-to-5-8-ghz-lga1700-unlocked-desktop-processor/6521190.p?skuId=6521190"
    
    attempt = 0
    item_details = None
    while(not item_details):
        item_details = get_item_details(URL)
        if(not item_details):
            print('Time:' + str(datetime.now()), "Attempt:" + str(attempt))
            attempt+=1
            time.sleep(5)
        else:
            print(item_details)
            publish(item_details)

def publish(details):
    arn = 'arn:aws:sns:us-east-1:270154753373:inStock'
    sns_client = boto3.client(
        'sns',
        aws_access_key_id=os.getenv("AWSAccessKeyId"),
        aws_secret_access_key=os.getenv("AWSSecretKey"),
        region_name = 'us-east-1'
    )

    response = sns_client.publish(TopicArn = arn, Message=details)
    print(response)

def get_item_details(URL):
    #if button does not say in stock, return None
    #else look through json and return the cost and discount of the item
    header = {
        'authority': 'www.bestbuy.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'accept-language': 'en-US,en;q=0.9',

    }

    page = requests.get(URL, headers = header)
    soup = BeautifulSoup(page.content, 'html.parser')
    stock = soup.find('button', class_='c-button c-button-disabled c-button-lg c-button-block add-to-cart-button')
    if(stock):
        print(stock.text)
        return None
    
    price = soup.find('div', class_='priceView-hero-price priceView-customer-price')


    print(price.text.split('.')[0])
    
    return price.text.split('.')[0]


if __name__ == "__main__":
    main()