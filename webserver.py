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
    s = ""
    for r in query:
        s += f"{r.name} || <a href='/restaurant/{r.id}/edit'> edit </a>||<a href='/delete/{r.name}'> delete </a>||</br>"

    s += "\n<a href='/restaurant/new'>Create New Restaurant</a>"
    return s



@bottle.route("/delete/<name>")
def delete(name):
    s = f"Are you sure you want to delete {name}?<br><a href='/confirm/delete/{name}'>Yes</a> || <a href='/restaurant'>No</a>"
    return s


@bottle.route("/confirm/delete/<name>")
def deleted(name):
    query = session.query(Restaurant).filter_by(name=str(name)).one()
    print(query)
    session.delete(query)
    bottle.redirect("/restaurant")


@bottle.get('/restaurant/new')
def get_new_restaurant():
    return f"""
           <form action="/restaurant/new" method="post">
            Restaurant Name: <input name="restaurant_name" type="text" />
            <input value="Submit" type="submit" />
        </form>
        """


@bottle.post('/restaurant/new')
def post_new_restaurant():
    rname = bottle.request.forms.get("restaurant_name")
    new_rest = Restaurant(name=rname)
    session.add(new_rest)
    session.commit()
    bottle.redirect("/restaurant")


@bottle.get('/restaurant/<id>/edit')
def edit_restaurant(id):
    target = session.query(Restaurant).filter_by(id=int(id)).one()
    return f"""
<form action="/restaurant/{id}/edit" method="post">
Restaurant Name: <input name="restaurant_name" type="text" value="{target.name}"/>
<input value="Submit" type="submit"/>
</form>"""


@bottle.post('/restaurant/<id>/edit')
def confirm_edit_restaurant(id):
    target = session.query(Restaurant).filter_by(id=int(id)).one()
    new_name = bottle.request.forms.get("restaurant_name")
    target.name = new_name
    session.commit()
    bottle.redirect("/restaurant")


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

bottle.run(app=None, server='wsgiref', host='localhost', port=80, interval=1, reloader=True, quiet=False, plugins=None, debug=None)
