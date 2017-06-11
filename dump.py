import local_secrets
import dataset

db = dataset.connect(local_secrets.CONNECTION_STRING)

result = db[local_secrets.TABLE_NAME].all()
dataset.freeze(result, format='csv', filename=local_secrets.CSV_NAME)