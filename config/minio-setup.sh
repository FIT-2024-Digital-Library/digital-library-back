mc alias set local http://lib-minio:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
mc admin user add local $MINIO_LOGIN $MINIO_PASSWORD
mc admin policy attach local readwrite --user $MINIO_LOGIN
mc mb $MINIO_VOLUMES/$MINIO_BUCKET_NAME
