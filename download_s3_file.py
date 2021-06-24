import boto3
from botocore.exceptions import NoCredentialsError

ACCESS_KEY = 'dfasdfasdf'
SECRET_KEY = 'sdfasdf+asdfasd'


def download_from_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)

    try:
        s3.download_file(bucket,s3_file, local_file)
        print("download Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False



v_local_fie='C:/Users/Acer Aspire 5/PycharmProjects/pythonProject/practice/file_from_s3_email.py'

uploaded = download_from_aws(v_local_fie, 'vvbr52bucket', 'send_email.py')
