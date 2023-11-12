import json
import inflection
import boto3
import botocore
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
es_client = boto3.client('opensearch')
# HOST = 'search-photos-dhul7pceqzrodplgllu4qk25jy.us-east-1.es.amazonaws.com/'

# this one is use for testing opensearch cloud formation.
HOST = 'search-photos1-sxipfgbn7hxqx3ibsnr3lvxany.us-east-1.es.amazonaws.com/'
REGION = 'us-east-1'
INDEX = 'photos'

def lambda_handler(event, context):
    # TODO implement
    print(event)
    try:
        # Use the head_object method to get S3 object metadata
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        response = s3.head_object(Bucket=bucket, Key=key)
        
        print(response)
        
        
        rekognition_response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': str(key)
                }
            }
        )

        
        labels = [label['Name'] for label in rekognition_response['Labels']]
        cusomLabels = response["Metadata"]["customlabels"]
        
        for label in labels:
            label = inflection.singularize(label)
        if customlabels != "":
            customlabels = customlabels.split(",")
            for l in customlabels:
                labels.append(inflection.singularize(l))
        
        print(labels)
        print(response)
        
        json_data = {}
        json_data['objectKey'] = key
        json_data['bucket'] = bucket
        # json_data['createdTimestamp'] = response["Metadata"]["uploadtime"]
        json_data['createdTimestamp'] = ""
        json_data['labels'] = labels
        
        print(json_data)
        json_object = json.dumps(json_data)
        print(json_object)
        
        insert(json_object)

    except botocore.exceptions.ClientError as e:
        print(f'Error: {str(e)}')
        return {
            'statusCode': 500,
            'body': 'Error retrieving S3 metadata.'
        }
    # s3 = boto3.client('s3')
    # response = s3.head_object(Bucket='photoalbumsb2', Key='1.png')
    # print(response)
    return {
        'statusCode': 200,
        'body': '',
        "headers": {
                "Content-Type": 'application/json',
                "Access-Control-Allow-Headers": '*',
                "Access-Control-Allow-Origin": '*',
                "Access-Control-Allow-Methods": '*',
        }
    }



def insert(json_object):
    

    client = OpenSearch(hosts=[{
        'host': es_client.describe_domain(DomainName=INDEX)['DomainStatus']['Endpoint'],
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)


    client.index(index=INDEX, body=json_object)
    print("insert successfully.")

def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)