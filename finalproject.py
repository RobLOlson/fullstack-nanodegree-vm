import gspread, shelve, time, random
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

spreadsheet = client.open("restaurant_db")
sheet_r = spreadsheet.worksheet("restaurants")  # Open the spreadhseet
sheet_m = spreadsheet.worksheet("menu_items")  # Open the spreadhseet
sheet_time = spreadsheet.worksheet("time_stamp")

local_db = {}

# update_r = sheet_time.cell(2, 1)
# update_m = sheet_time.cell(2, 2)


class GRestaurant(object):
    def __init__(self, name, id):
        self.name = name
        self.id = id

    @property
    def serialize(self):
        return {
            "name" : self.name,
            "id" : self.id
        }

class GMenu_Item(object):
    def __init__(self, name, id, price=None, description=None, restaurant_id=None):
        self.name = name
        self.id = id
        self.price = price
        self.description = description
        self.restaurant_id = restaurant_id

    @property
    def serialize(self):
        return {
            "name" : self.name,
            "id" : self.id,
            "price" : self.price,
            "description" : self.description,
            "restaurant_id" : self.restaurant_id
        }

@app.route("/")
@app.route("/restaurants/")
def all_restaurants():
    global local_db
    return render_template("allrestaurants.html", local_db = local_db)

@app.route("/restaurant/<restaurant_id>/")
@app.route("/restaurant/<restaurant_id>/menu/")
def restaurant_menu(restaurant_id):
    global local_db

    items = []

    for key in local_db.keys():
        if "menuid" in key:
            if local_db[key].restaurant_id == restaurant_id:
                items.append(local_db[key])

    return render_template("menu.htm", restaurant=local_db[restaurant_id], items=items)

@app.route("/restaurant/<restaurant_id>/edit/", methods=["GET", "POST"])
def edit_restaurant(restaurant_id):
    global local_db
    global sheet_r
    global sheet_m
    global sheet_time

    restaurant = local_db[restaurant_id]

    if request.method == "POST":
        time_stamp = time.time()
        target_row = sheet_r.find(restaurant.id).row
        sheet_r.update_cell(target_row, 1, value=request.form['name'])
        sheet_time.update_cell(1, 1, time_stamp)

        local_db[restaurant.id].name = request.form['name']

        with shelve.open("database") as db:
            db[restaurant.id].name = request.form['name']

        return redirect(url_for("all_restaurants"))

    else:
        return render_template("editrestaurant.html", restaurant=restaurant)

@app.route("/restaurant/<restaurant_id>/delete/", methods=["GET", "POST"])
def delete_restaurant(restaurant_id):
    global local_db
    global sheet_r
    global sheet_time

    restaurant = local_db[restaurant_id]

    if request.method == "POST":
        return "POSTED"
    else:
        return render_template("deleterestaurant.html", restaurant=restaurant)

@app.route("/restaurant/new/", methods=["GET", "POST"])
def new_restaurant():
    global local_db
    global sheet_r
    global sheet_time

    if request.method == "POST":
        new_id = 1
        time_stamp = time.time()

        while "restaurantid"+str(new_id) in local_db.keys():
            new_id = random.randint(1, 1000000)

        new_id = "restaurantid"+str(new_id)

        sheet_r.append_row([request.form["name"], new_id])
        sheet_time.update_cell(1, 1, time_stamp)
        local_db[new_id] = GRestaurant(request.form["name"], new_id)
        return redirect(url_for("all_restaurants"))
    else:
        return render_template("newrestaurant.html")

@app.route("/restaurant/<restaurant_id>/menu/new/")
def new_menu_item(restaurant_id):
    return "new menu item"

@app.route("/restaurant/<restaurant_id>/menu/<menu_id>/edit/")
def edit_menu_item(restaurant_id, menu_id):
    return "edit menu item"

@app.route("/restaurant/<restaurant_id>/menu/<menu_id>/delete/")
def delete_menu_item(restaurant_id, menu_id):
    return "delete menu item"

def full_update_local():
    global sheet_r
    global sheet_m
    global sheet_time
    global last_updated_time_stamp
    global local_db

    r_dict = sheet_r.get_all_records(head=1)
    m_dict = sheet_m.get_all_records(head=1)

    with shelve.open("database") as db:
        for row in r_dict:
            db[row["id"]] = GRestaurant(row["name"], row["id"])

        for row in m_dict:
            db[row["id"]] = GMenu_Item(name=row["name"],
                                       id=row["id"],
                                       price=row["price"],
                                       description=row["description"],
                                       restaurant_id=row["restaurant_id"])

        db["last_updated_time_stamp"] = int(sheet_time.cell(1,1).value)
        last_updated_time_stamp = db["last_updated_time_stamp"]
        local_db = dict(db)

with shelve.open("database") as db:
    last_updated_time_stamp = db.get("last_updated_time_stamp", 0)
    local_db = dict(db)

if int(last_updated_time_stamp) < int(sheet_time.cell(1, 1).value):
   full_update_local()


if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000)
