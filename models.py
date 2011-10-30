from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import String, Integer
import time

from framework import Base

import simplejson as json 
 
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    
    def __init__(self, username):
        Base.__init__(self)
        self.username = username

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    
    def __init__(self, product_id, name, url):
        self.id = product_id
        self.name = name
        self.url = url

class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    value = Column(Integer)
    timestamp = Column(Integer)
    
    user = relationship("User", backref=backref('votes', order_by=id))
    product = relationship("Product", backref=backref('votes', order_by=id))
    
    def __init__(self, product, user, value, timestamp=None):
        self.product = product
        self.user = user
        self.value = value
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = time.time()
