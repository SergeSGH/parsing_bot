from pony.orm import Database, Required

db = Database()
db.bind(provider='sqlite', filename='parsing_data.sqlite3', create_db=True)


class Sites(db.Entity):
    name = Required(str)
    url = Required(str)
    xpath = Required(str)


def init():
    db.generate_mapping(create_tables=True)
