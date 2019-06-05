from flask import Flask, render_template, request, redirect, url_for

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from database_setup import Base, Restaurant, MenuItem

app = Flask(__name__)
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/restaurants/')
def all_restaurants():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    restaurants = session.query(Restaurant).all()
    output = ""
    for r in restaurants:
        output += f"<p><a href='/restaurant/{r.id}/menu/'>{r.name}</a></p></br>"

    return output


@app.route('/restaurant/<int:restaurant_id>/menu/')
def restaurantMenu(restaurant_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    return render_template('menu.htm', restaurant=restaurant, items=items)

# Task 1: Create route for newMenuItem function here
@app.route("/restaurant/<int:restaurant_id>/new/", methods=['GET','POST'])
def new_menu_item(restaurant_id):
    if request.method =='POST':
        new_Item = MenuItem(name = request.form['name'],
                            restaurant_id=restaurant_id)
        session.add(new_Item)
        session.commit()
        return redirect(url_for('restaurantMenu',
                                 restaurant_id=restaurant_id))

    else:
        return render_template('newmenuitem.html',
                               restaurant_id=restaurant_id)

# Task 2: Create route for editMenuItem function here

@app.route("/restaurant/<int:restaurant_id>/<int:menu_id>/edit/", methods=['GET', 'POST'])
def edit_menu_item(restaurant_id, menu_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    menu_item = session.query(MenuItem).filter_by(id=menu_id).one()
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method =='POST':
        menu_item.name = request.form['name']
        menu_item.description = request.form['description']
        menu_item.price = request.form['price']
        session.commit()
        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))

    else:
        return render_template('editmenuitem.html',
                               restaurant=restaurant,
                               menu_item=menu_item)

# Task 3: Create a route for deleteMenuItem function here

@app.route("/restaurant/<int:restaurant_id>/<int:menu_id>/delete/")
def delete_menu_item(restaurant_id, menu_id):

    return "page to delete a menu item. Task 3 complete!"

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
