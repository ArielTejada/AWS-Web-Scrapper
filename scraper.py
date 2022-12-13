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

    items = consolidate(scan_table(table))#items is a list of dictionaries that has ['URL'] = string url, ['Emails'] = list of emails

    arn_name = len(list_topics(sns_client))

    for item in items:
        if len(item) == 2:
            arn = create_topic("bingbong" + str(arn_name), sns_client)
            arn_name +=1
            if arn:
                item['arn'] = arn
                subscribe(item['arn']['TopicArn'], item['Emails'], sns_client)

    # def updateData(items):
    #     while(True):
    #         items.clear()
    #         dynamodb = boto3.resource('dynamodb',
    #             region_name='us-east-1',
    #             endpoint_url='https://dynamodb.us-east-1.amazonaws.com',
    #             aws_access_key_id=os.getenv("AWSAccessKeyId"),
    #             aws_secret_access_key=os.getenv("AWSSecretKey"),
    #         )

    #         table = dynamodb.Table('Scraper')

    #         temp = consolidate(scan_table(table) + items)#items is a list of dictionaries that has ['URL'] = string url, ['Emails'] = list of emails

    #         arn_name = len(list_topics(sns_client))

    #         for item in temp:
    #             if len(item) == 2:
    #                 arn = create_topic("bingbong" + str(arn_name), sns_client)
    #                 arn_name +=1
    #                 if arn:
    #                     item['arn'] = arn
    #                     subscribe(item['arn']['TopicArn'], item['Emails'], sns_client)
    #         items+=temp
    #         time.sleep(3600)


    # # print(items)

    # x = threading.Thread(target=updateData, args=(items,))
    # x.start()

    # attempt = 0
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
                publish(item_details, sns_client, items[counter]['arn']['TopicArn'])
                delete_topic(sns, items[counter]['arn']['TopicArn'])
                delete_item(items[counter], table)
                items.pop(counter)
                counter = 0



def delete_item(item,table):
    for i in range(len(item['Emails'])):
        table.delete_item(
            Key={
                'URL': item['URL'],
                'Email': item['Emails'][i]
            }
        )

def consolidate(items):
    d = defaultdict(list)
    for item in items:
        d[item['URL']].append(item['Email'])

    res = []

    for key in d.keys():
        res.append({'URL' : key, 'Emails' : d[key]})

    return res

def list_topics(sns_client):
    """
    Lists all SNS notification topics using paginator.
    """
    try:

        paginator = sns_client.get_paginator('list_topics')

        # creating a PageIterator from the paginator
        page_iterator = paginator.paginate().build_full_result()

        topics_list = []

        # loop through each page from page_iterator
        for page in page_iterator['Topics']:
            topics_list.append(page['TopicArn'])
    except ClientError:
        print(f'Could not list SNS topics.')
    else:
        return topics_list

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



def create_topic(name, sns_client):
    """
    Creates a SNS notification topic.
    """
    try:
        topic = sns_client.create_topic(Name=name)

    except ClientError:
        print(f'Could not create SNS topic {name}.')
    else:
        return topic

def subscribe(topic, endpoints, sns_client):
    """
    Subscribe to a topic using endpoint as email OR SMS
    """
    for endpoint in endpoints:
        try:
            subscription = sns_client.subscribe(
                TopicArn=topic,
                Protocol="email",
                Endpoint=endpoint,
                ReturnSubscriptionArn=True)['SubscriptionArn']
        except ClientError:
            print(
                "Couldn't subscribe {protocol} {endpoint} to topic {topic}.")
        else:
            return subscription



#this will scan the entire database and print the contents
def scan_table(table):
    response = table.scan()
    items = response['Items']
    return items

def publish(details, sns_client, arn):
    response = sns_client.publish(TopicArn = arn, Message=details)
    print(response)

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

    # print(price.text.split('.')[0])
    
    return URL + " " + price.text.split('.')[0]


if __name__ == "__main__":
    main()