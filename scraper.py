import os
from dotenv import load_dotenv
import requests
import boto3
from bs4 import BeautifulSoup
from datetime import date, datetime
import time
from botocore.exceptions import ClientError
import urllib3
import threading

from collections import defaultdict

def main():
    load_dotenv()

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    sns_client = boto3.client(
      'sns',
      aws_access_key_id=os.getenv("AWSAccessKeyId"),
      aws_secret_access_key=os.getenv("AWSSecretKey"),
      region_name = 'us-east-1'
    )


    sns = boto3.resource('sns', region_name = 'us-east-1',
        aws_access_key_id=os.getenv("AWSAccessKeyId"),
        aws_secret_access_key=os.getenv("AWSSecretKey")
    )

    dynamodb = boto3.resource('dynamodb',
        region_name='us-east-1',
        endpoint_url='https://dynamodb.us-east-1.amazonaws.com',
        aws_access_key_id=os.getenv("AWSAccessKeyId"),
        aws_secret_access_key=os.getenv("AWSSecretKey"),
    )

    table = dynamodb.Table('Scraper')

    items = scan_table(table)#items is a list of dictionaries that has ['URL'] = string url, ['Emails'] = list of emails

    def updateData(items):
        while(True):
            items.clear()
            dynamodb = boto3.resource('dynamodb',
                region_name='us-east-1',
                endpoint_url='https://dynamodb.us-east-1.amazonaws.com',
                aws_access_key_id=os.getenv("AWSAccessKeyId"),
                aws_secret_access_key=os.getenv("AWSSecretKey"),
            )

            table = dynamodb.Table('Scraper')

            items += scan_table(table)

            time.sleep(3600)

    x = threading.Thread(target=updateData, args=(items,))
    x.start()

    item_details = None
    counter = 0
    while(True):
        while(len(items) != 0):
            if counter > len(items) -1:
                    counter = 0
            URL = items[counter]['URL']
            item_details = get_item_details(URL)
            print(URL, "\n")
            if(not item_details):
                counter+=1
                
            else:
                publish(item_details, sns_client, items[counter]['Arn'])
                time.sleep(2)
                delete_topic(sns, items[counter]['Arn'])
                delete_item(items[counter], table)
                items.pop(counter)
                counter = 0

def delete_item(item,table):
    table.delete_item(
        Key={
            'URL': item['URL'],
            'Email': item['Email'],
            # 'Arn' : item['Arn']
        }
    )

def delete_topic(sns, arn):
    """
    Deletes a topic. All subscriptions to the topic are also deleted.
    """
    try:
        topic = sns.Topic(arn)

        topic.delete()
        print("Deleted topic %s.", topic.arn)
    except ClientError:
        print("Couldn't delete topic %s.", topic.arn)

#this will scan the entire database and print the contents
def scan_table(table):
    response = table.scan()
    items = response['Items']
    return items

def publish(details, sns_client, arn):
    try:
        response = sns_client.publish(TopicArn = arn, Message=details)
        print(response)
    except:
        print("Could not publish")

def get_item_details(URL):
    #if button does not say in stock, return None
    #else look through json and return the cost and discount of the item

    proxy = {
        'https': '198.59.191.234:8080',
    }
    header = {
        'authority': 'www.bestbuy.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'accept-language': 'en-US,en;q=0.9',

    }

    page = requests.get(URL, headers = header, proxies= proxy,verify=False)

    soup = BeautifulSoup(page.content, 'html.parser')
    stock = soup.find('button', class_='c-button c-button-disabled c-button-lg c-button-block add-to-cart-button')
    if(stock):
        print(stock.text)
        return None
    
    price = soup.find('div', class_='priceView-hero-price priceView-customer-price')

    if not price:
        return

    return URL + " " + price.text.split('.')[0]


if __name__ == "__main__":
    main()