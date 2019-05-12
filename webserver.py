#!/usr/bin/env python3
import bottle

from database_setup import *

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Session = sessionmaker(bind=engine)
session = Session()

@bottle.route("/restaurant")
def restaurant():
    query = session.query(Restaurant).all()
    print(f'{[r.name for r in query]}')

#print all rows
#for row in session.query(Restaurant)
#   print(row)
#
#print the the 10 rows with smallest id
#for row in session.query(Restaurant).order_by(Restaurant.id)[:10]
#   print(row)
#
#print only name & id
#for name, id in session.query(Restaurant.name, Restaurant.id)
#   print(f'{name}, {id}')
#
#print restaurants named McDonalds and Burger King
#for row in session.query(Restaurant).filter(Restaurant.name.in_(['McDonalds', 'Burger King'])):
#   print(row)
#
#gives the number of restaurants named Taco Bell
#session.query(Restaurant).filter(Restaurant.name.like("Taco Bell")).count()

# @bottle.route('/restaurant')
# def restaurant(name):

#     return f'<b>hello {name}</b>!!'

# run(host='localhost', port=80, debug=True)

bottle.run(app=None, server='wsgiref', host='127.0.0.1', port=80, interval=1, reloader=False, quiet=False, plugins=None, debug=None)
