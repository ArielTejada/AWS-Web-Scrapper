import env
import requests
import json
import boto3
from datetime import datetime
import time

URL = 'https://www.bestbuy.ca/ecomm-api/availability/products?accept=application%2Fvnd.bestbuy.standardproduct.v1%2Bjson&accept-language=en-CA&locations=203%7C977%7C617%7C62%7C931%7C927%7C57%7C938%7C965%7C237%7C932%7C202%7C943%7C200%7C956%7C926%7C795%7C916%7C233%7C544%7C910%7C954%7C207%7C930%7C937%7C622%7C245%7C223%7C990%7C925%7C985%7C206%7C942%7C949%7C959&postalCode=M6J&skus=13444247'

headers = {
	'authority': 'www.bestbuy.ca',
	'pragma': 'no-cache',
	'cache-control': 'no-cache',
	'user-agent': 'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4159.2 Safari/537.36',
	'accept': '*/*',
	'sec-fetch-site': 'same-origin',
	'sec-fetch-mode': 'cors',
	'sec-fetch-dest': 'empty',
	'referer': 'https://www.bestbuy.ca/en-ca/product/logitech-c920s-pro-1080p-hd-webcam/13444247',
	'accept-language': 'en-US,en;q=0.9'
}

def main():
    quantity = 0
    attempt = 0

    while (quantity < 1):
        response = requests.get(URL, headers=headers)
        response_formatted = json.loads(response.content.decode('utf-8-sig').encode('utf-8'))

        quantity = response_formatted['availabilities'][0]['shipping']['quantityRemaining']

        if (quantity < 1):
            #Out Of stock
            print('Time=' + str(datetime.now()) + "- Attempt=" + str(attempt))
            attempt += 1
            time.sleep(5)
        else:
            print('Hey its in stock! Quantity=' + str(quantity))
            publish(quantity)


def publish(quantity):
    arn = 'arn:aws:sns:us-east-1:398447858632:InStockTopic'
    sns_client = boto3.client(
        'sns',
        aws_access_key_id=env.accessKey,
        aws_secret_access_key=env.secretKey,
        region_name='us-east-1'
    )

    response = sns_client.publish(TopicArn=arn, Message='Its in stock! Quantity=' + str(quantity))
    print(response)

main()