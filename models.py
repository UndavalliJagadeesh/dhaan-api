class User(db.Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    group = Column(String)


class Transact(db.Model):
    __tablename__ = 'transact'
    user_id = Column(Integer, db.ForeignKey('user.id'), primary_key=True)
    type = Column(String)
    # amount = Column(Integer)
    loc = Column(String)
