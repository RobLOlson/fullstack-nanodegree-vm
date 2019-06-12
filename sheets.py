from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
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

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)
spreadsheet = client.open("restaurant_db")

r_sheet = spreadsheet.worksheet("restaurants")  # Open the spreadhseet
m_sheet = spreadsheet.worksheet("menu_items")  # Open the spreadhseet


class GRestaurant(object):
    def __init__(self, name, id):
        self.name = name
        self.id = id

    @property
    def serialize(self):
        #Returns object data in easily serializeable format
        return {
            'name' : self.name,
            'id' : self.id
        }

class GMenu_Item(object):
    def __init__(self, name, id, price="", description="", restaurant_id=0):
        self.name = name
        self.id = id
        self.price = price
        self.description = description
        self.restaurant_id = restaurant_id

    @property
    def serialize(self):
        #Returns easily serializeable dictionary
        return {
            'name' : self.name,
            'description' : self.description,
            'id' : self.id,
            'price' : self.price,
            'restaurant_id' : self.restaurant_id
        }

@app.route('/')
@app.route('/restaurants/')
def all_restaurants():
    global r_sheet
    global m_sheet

    output = ""
    for r in r_sheet.get_all_records():
        output += f"""<p><a href='/restaurant/{r['id']}/menu/'>{r['name']}</a></p></br>"""

    return output

@app.route('/restaurant/<restaurant_id>/')
@app.route('/restaurant/<restaurant_id>/menu/')
def restaurantMenu(restaurant_id):
    global r_sheet
    global m_sheet

    target_row = r_sheet.find(f"{restaurant_id}").row
    restaurant_row = r_sheet.row_values(target_row)
    restaurant = GRestaurant(*restaurant_row)

    items = []

    for cell in m_sheet.findall(f"{restaurant_id}"):
        target_row = m_sheet.row_values(cell.row)
        items.append(GMenu_Item(*target_row))

    # restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    # items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    return render_template('menu.htm', restaurant=restaurant, items=items)

# Task 1: Create route for newMenuItem function here
@app.route("/restaurant/<restaurant_id>/new/", methods=['GET','POST'])
def new_menu_item(restaurant_id):
    global r_sheet
    global m_sheet

    target_row = r_sheet.find(f"{restaurant_id}").row
    restaurant_row = r_sheet.row_values(target_row)
    restaurant = GRestaurant(*restaurant_row)

    items = []

    for cell in m_sheet.findall(f"{restaurant_id}"):
        target_row = m_sheet.row_values(cell.row)
        items.append(GMenu_Item(*target_row))


    if request.method == 'POST':
        new_id = m_sheet.row_count+1

        m_sheet.append_row([request.form['name'], f"menuid{new_id}", "$1000", "Yummy", restaurant_id])
        flash(f"new menu item ({request.form['name']}) created!")
        # new_Item = MenuItem(name = request.form['name'],
        #                     restaurant_id=restaurant_id)
        # session.add(new_Item)
        # session.commit()
        return redirect(url_for('restaurantMenu',
                                 restaurant_id=restaurant_id))

    else:
        return render_template('newmenuitem.html',
                               restaurant_id=restaurant_id)

# Task 2: Create route for editMenuItem function here

@app.route("/restaurant/<restaurant_id>/<menu_id>/edit/", methods=['GET', 'POST'])
def edit_menu_item(restaurant_id, menu_id):
    global r_sheet
    global m_sheet

    target_row_m = m_sheet.find(f"{menu_id}").row
    menu_item = GMenu_Item(*m_sheet.row_values(target_row_m))

    target_row_r = r_sheet.find(f"{restaurant_id}").row
    restaurant = GRestaurant(*r_sheet.row_values(target_row_r))

    # menu_item = session.query(MenuItem).filter_by(id=menu_id).one()
    # restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        cells_to_update = m_sheet.range(target_row_m, 1, target_row_m, 5)
        cells_to_update[0].value = request.form['name']
        cells_to_update[2].value = request.form['price']
        cells_to_update[3].value = request.form['description']
        m_sheet.update_cells(cells_to_update)
        flash(f"Updated menu item ({menu_item.name}).")
        # menu_item.name = request.form['name']
        # menu_item.description = request.form['description']
        # menu_item.price = request.form['price']
        # session.commit()
        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))

    else:
        return render_template('editmenuitem.html',
                               restaurant=restaurant,
                               menu_item=menu_item)

# Task 3: Create a route for deleteMenuItem function here

@app.route("/restaurant/<restaurant_id>/<menu_id>/delete/", methods=['GET', 'POST'])
def delete_menu_item(restaurant_id, menu_id):
    global r_sheet
    global m_sheet

    target_row_m = m_sheet.find(f"{menu_id}").row
    menu_item = GMenu_Item(*m_sheet.row_values(target_row_m))

    target_row_r = r_sheet.find(f"{restaurant_id}").row
    restaurant = GRestaurant(*r_sheet.row_values(target_row_r))


    # menu_item = session.query(MenuItem).filter_by(id=menu_id).one()
    # restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()

    if request.method == 'POST':
        m_sheet.delete_row(target_row_m)
        flash(f"Deleted menu item({menu_item.name}).")
        # session.delete(menu_item)
        # session.commit()
        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:
        return render_template('deletemenuitem.html',
                               restaurant=restaurant,
                               menu_item=menu_item)

#         return f"""
# <form action = "/restaurant/{restaurant_id}/{menu_id}/delete/" method = "POST">
# <input type='submit' value='CONFIRM DELETE'>
# </form>
#         """

@app.route('/restaurant/<restaurant_id>/menu/JSON/')
def restaurantMenuJSON(restaurant_id):
    global r_sheet
    global m_sheet

    target_row = r_sheet.find(f"{restaurant_id}").row
    restaurant_row = r_sheet.row_values(target_row)
    restaurant = GRestaurant(*restaurant_row)

    items = []

    for cell in m_sheet.findall(f"{restaurant_id}"):
        target_row = m_sheet.row_values(cell.row)
        items.append(GMenu_Item(*target_row))

    return jsonify(menu_items=[i.serialize for i in items])


@app.route('/restaurant/<restaurant_id>/menu/<menu_id>/JSON/')
def menu_item_JSON(restaurant_id, menu_id):
    global m_sheet

    target_row_m = m_sheet.find(f"{menu_id}").row
    menu_item = GMenu_Item(*m_sheet.row_values(target_row_m))

    return jsonify(menu_item=menu_item.serialize)

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000)
