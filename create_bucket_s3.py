import boto3
from botocore.exceptions import NoCredentialsError

ACCESS_KEY = 'ssdfasd'
SECRET_KEY = 'asdfasdf+asdfasd'

def create_bucket_s3(bucket):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)

    try:
        s3.create_bucket(Bucket=bucket)
        print("Bucket is created")
        return True
    except FileNotFoundError:
        print("Error in credentials")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False


uploaded = create_bucket_s3('vvbr52bucket2')
