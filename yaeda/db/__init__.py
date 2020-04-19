from .models import Base

import sqlalchemy
import sqlalchemy.orm as orm
import os


engine = sqlalchemy.create_engine(os.environ.get('DATABASE_URL', 'sqlite:///:memory:'))

Base.metadata.create_all(engine)

Session = orm.sessionmaker(engine)
db_session = Session()
