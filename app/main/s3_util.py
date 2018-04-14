#created by Shikang Xu
import uuid
import boto3
import os
from flask import current_app
from werkzeug.utils import secure_filename

def s3_upload(source_file, upload_dir=None, acl='public-read'):
    if upload_dir is None:
        upload_dir=current_app.config["S3_BUCKET"]
    source_filename=secure_filename(source_file.filename)
    source_extension=os.path.splitext(source_filename)[1]

    source_file.filename=uuid.uuid4().hex + source_extension
    s3 = boto3.client("s3", aws_access_key_id=current_app.config["S3_KEY"],aws_secret_access_key=current_app.config["S3_SECRET"])

    try:
        s3.upload_fileobj(source_file, upload_dir, current_app.config['PIC_FOLDER']+'/'+source_file.filename,ExtraArgs={
                'ACL': acl, "ContentType": source_file.content_type}
                          )
    except Exception as e:
        print("s3 error")
        print(e)
        return e
    return source_file.filename

def s3_delete(filename,upload_dir=None):
    if upload_dir is None:
        upload_dir=current_app.config["S3_BUCKET"]
    filename=secure_filename(filename)
    s3 = boto3.client("s3", aws_access_key_id=current_app.config["S3_KEY"],
                      aws_secret_access_key=current_app.config["S3_SECRET"])
    print(filename)
    print(upload_dir)
    # print(current_app.config['PIC_FOLDER'])
    # print(current_app.config(['PIC_FOLDER'])+'/'+filename)
    try:
        s3.delete_object(Bucket=upload_dir,Key=current_app.config['PIC_FOLDER']+'/'+filename)
    except Exception as e:
        print('s3 delete error')
        print(e)