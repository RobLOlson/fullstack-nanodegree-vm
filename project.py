from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)


from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from database_setup import Base, Restaurant, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)
spreadsheet = client.open("restaurant_db")

r_sheet = spreadsheet.worksheet("restaurants")  # Open the spreadhseet
m_sheet = spreadsheet.worksheet("menu_items")  # Open the spreadhseet

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

@app.route("/restaurant/<int:restaurant_id>/<int:menu_id>/delete/", methods=['GET', 'POST'])
def delete_menu_item(restaurant_id, menu_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    menu_item = session.query(MenuItem).filter_by(id=menu_id).one()
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()

    if request.method == 'POST':
        # session.delete(menu_item)
        # session.commit()
        breakpoint()
        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:
        # return render_template('editmenuitem.html',
        #                        restaurant=restaurant,
        #                        menu_item=menu_item)

        # return render_template('deletemenuitem.html',
                               # restaurant=restaurant,
                               # menu_item=menu_item)

        return f"""
<form action = "/restaurant/{restaurant_id}/{menu_id}/delete" form = "POST">
<a href="/restaurant/{restaurant_id}/{menu_id}/delete"><input type='button' value='CONFIRM DELETE'></a>
</form>
        """

@app.route("/export/")
def export():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    r_sheet = spreadsheet.worksheet("restaurants")  # Open the spreadhseet
    m_sheet = spreadsheet.worksheet("menu_items")  # Open the spreadhseet


    spreadsheet.del_worksheet(r_sheet)
    spreadsheet.del_worksheet(m_sheet)

    r_sheet = spreadsheet.add_worksheet("restaurants", 1000, 5)
    m_sheet = spreadsheet.add_worksheet("menu_items", 1000, 5)

    for row in session.query(Restaurant).all():
        new_row = [row.name, row.id]
        r_sheet.insert_row(new_row)

    for row in session.query(MenuItem).all():
        new_row = [row.name, row.id, row.price, row.description, row.restaurant_id]
        m_sheet.insert_row(new_row)

    return "EXPORT SUCCESSFUL"

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
