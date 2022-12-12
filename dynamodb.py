import boto3
from boto3.dynamodb.conditions import Key, Attr


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Scraper')

def add_item(url,email):
    table.put_item(
        Item={
            'URL': url,#change to variable to take user input
            'Email': email,#change to variable to take user input
        }
    )

def delete_item(url,email):
    table.delete_item(
        Key={
            'URL': url,
            'Email': email
        }
    )

#this will query specific entries 
def query_table(url):
    response = table.query(
        KeyConditionExpression=Key('URL').eq(url) #eq is equal to the key value
    )
    items = response['Items']
    print(items)

#this will scan the entire database and print the contents
def scan_table():
    response = table.scan()
    items = response['Items']
    print(items)
