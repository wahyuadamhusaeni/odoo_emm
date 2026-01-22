#!/bin/bash
echo "Backup started at `date +%Y%m%d_%H%M%S`"
TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
BASE_DIR=/home/admin/Projects/odoo_prod/db_backup
DB_USER=odoo_user3
DB_NAME=PROD_MASTER
DB_PASS=3k4m4ju1982
LOG_FILE=./buOdoo.log
if [ $# -eq 1 ]
then
    FILENAME=ODOO_`date +%Y%m%d_%H%M%S`_$1.sql
else
    FILENAME=ODOO_`date +%Y%m%d_%H%M%S`.sql
fi

# pg_dump -U $DB_USER --no-owner --no-privileges --no-password --create --format=plain --verbose --file $BASE_DIR/$FILENAME $DB_NAME &> $LOG_FILE

PGPASSWORD=$DB_PASS pg_dump -U $DB_USER $DB_NAME > $BASE_DIR/$FILENAME

7za a -mx=9 $BASE_DIR/$FILENAME.7z $BASE_DIR/$FILENAME
ls -l $BASE_DIR/$FILENAME.7z
echo "Backup completed at `date +%Y%m%d_%H%M%S`"
