#---------Sambit (TPM) ----------------

from peewee import SqliteDatabase, Model, CharField

db = SqliteDatabase('secure_storage.db')

class SecureData(Model):
    data = CharField()

    class Meta:
        database = db

class SecureStorage:
    def __init__(self):
        db.connect()
        db.create_tables([SecureData], safe=True)

    def save_data(self, data):
        SecureData.create(data=data)

    def retrieve_data(self):
        return [item.data for item in SecureData.select()]
    
    def close_connection(self):
        if not db.is_closed():
            db.close()

    def delete_all_data(self):
        SecureData.delete().execute()