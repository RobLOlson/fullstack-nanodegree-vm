import gspread, shelve, time, random
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)

scope = ["https://spreadsheets.google.com/feeds",
         'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

spreadsheet = client.open("restaurant_db")
sheet_r = spreadsheet.worksheet("restaurants")  # Open the spreadhseet
sheet_m = spreadsheet.worksheet("menu_items")  # Open the spreadhseet
sheet_time = spreadsheet.worksheet("time_stamp")

local_db = {}


class GRestaurant(object):
    def __init__(self, name, id):
        self.name = name
        self.id = id

    @property
    def serialize(self):
        return {
            "name": self.name,
            "id": self.id
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
            "name": self.name,
            "id": self.id,
            "price": self.price,
            "description": self.description,
            "restaurant_id": self.restaurant_id
        }


@app.route("/")
@app.route("/restaurants/")
def all_restaurants():
    global local_db
    return render_template("allrestaurants.html", local_db=local_db)


@app.route("/restaurant/<restaurant_id>/")
@app.route("/restaurant/<restaurant_id>/menu/")
def restaurant_menu(restaurant_id):
    global local_db

    restaurant = local_db[restaurant_id]
    items = []

    for key in local_db.keys():
        if "menuid" in key:
            if local_db[key].restaurant_id == restaurant_id:
                items.append(local_db[key])

    return render_template("menu.htm", restaurant=restaurant, items=items)


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
        sheet_time.update_cell(1, 1, round(time_stamp))
        flash(f"Edited {restaurant.name}!")

        with shelve.open("database") as db:
            db[restaurant.id] = GRestaurant(request.form['name'], restaurant_id)
            local_db = dict(db)

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
        time_stamp = time.time()
        target_row = sheet_r.find(restaurant.id).row
        sheet_r.delete_row(target_row)
        sheet_time.update_cell(1, 1, round(time_stamp))
        flash(f"Deleted {restaurant.name}!")

        with shelve.open("database") as db:
            del db[restaurant.id]
            local_db = dict(db)

        return redirect(url_for("all_restaurants"))

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
        flash(f"Created new restaurant ({request.form['name']})!")

        with shelve.open("database") as db:
            db[new_id] = GRestaurant(request.form["name"], new_id)
            local_db = dict(db)
        return redirect(url_for("all_restaurants"))

    else:
        return render_template("newrestaurant.html")

@app.route("/restaurant/<restaurant_id>/menu/new/", methods=["GET", "POST"])
def new_menu_item(restaurant_id):
    global local_db
    global sheet_r
    global sheet_m
    global sheet_time

    restaurant = local_db[restaurant_id]

    if request.method == "POST":
        new_id = 1
        time_stamp = time.time()

        while "menuid"+str(new_id) in local_db.keys():
            new_id = random.randint(1, 1000000)

        new_id = "menuid"+str(new_id)

        new_menu_item = GMenu_Item(request.form["name"],
                                   new_id,
                                   request.form["price"],
                                   request.form["description"],
                                   restaurant_id)
        sheet_m.append_row([new_menu_item.name,
                            new_menu_item.id,
                            new_menu_item.price,
                            new_menu_item.description,
                            new_menu_item.restaurant_id])

        sheet_time.update_cell(1, 1, time_stamp)
        flash(f"Created new menu item for {restaurant.name} ({new_menu_item.name})!")

        with shelve.open("database") as db:
            db[new_id] = new_menu_item
            local_db = dict(db)

        return redirect(url_for("restaurant_menu", restaurant_id=restaurant.id))

    else:
        return render_template("newmenuitem.html", restaurant=restaurant)

@app.route("/restaurant/<restaurant_id>/menu/<menu_id>/edit/", methods=["GET", "POST"])
def edit_menu_item(restaurant_id, menu_id):
    global local_db
    global sheet_r
    global sheet_m
    global sheet_time

    restaurant = local_db[restaurant_id]
    menu_item = local_db[menu_id]

    if request.method == "POST":
        time_stamp = round(time.time())
        target_row = sheet_m.find(menu_id).row
        sheet_m.delete_row(target_row)
        sheet_m.append_row([request.form["name"],
                            menu_id,
                            request.form["price"],
                            request.form["description"],
                            restaurant_id])
        sheet_time.update_cell(1, 1, time_stamp)
        flash(f"Edited menu item in {restaurant.name} ({request.form['name']})!")

        with shelve.open("database") as db:
            db[menu_id] = GMenu_Item(request.form["name"],
                                     menu_id,
                                     request.form["price"],
                                     request.form["description"],
                                     restaurant_id)
            local_db = dict(db)

        return redirect(url_for("restaurant_menu", restaurant_id=restaurant_id))

    else:
        return render_template("editmenuitem.html", restaurant=restaurant, menu_item=menu_item)


@app.route("/restaurant/<restaurant_id>/menu/<menu_id>/delete/", methods=["GET", "POST"])
def delete_menu_item(restaurant_id, menu_id):
    global local_db
    global sheet_r
    global sheet_m
    global sheet_time

    restaurant = local_db[restaurant_id]
    menu_item = local_db[menu_id]

    if request.method == "POST":
        time_stamp = round(time.time())
        target_row = sheet_m.find(menu_id).row
        sheet_m.delete_row(target_row)
        sheet_time.update_cell(1, 1, time_stamp)
        flash(f"Deleted {restaurant.name} menu item ({menu_item.name})!")

        with shelve.open("database") as db:
            del db[menu_id]
            local_db = dict(db)

        return redirect(url_for("restaurant_menu", restaurant_id=restaurant_id))
    else:
        return render_template("deletemenuitem.html", restaurant=restaurant, menu_item=menu_item)

@app.route("/restaurants/JSON/")
def all_restaurants_JSON():
    global local_db

    restaurants = []

    for key in local_db.keys():
        if 'restaurantid' in key:
            restaurants.append(local_db[key])

    return jsonify(restaurants=[r.serialize for r in restaurants])

@app.route("/restaurant/<restaurant_id>/JSON/")
def restaurant_menu_JSON(restaurant_id):
    global local_db

    restaurant = local_db[restaurant_id]
    items = []

    for key in local_db.keys():
        if "menuid" in key:
            if local_db[key].restaurant_id == restaurant_id:
                items.append(local_db[key])

    return jsonify(menu_items=[i.serialize for i in items])


@app.route("/restaurant/<restaurant_id>/menu/<menu_id>/JSON/")
def menu_item_JSON(restaurant_id, menu_id):
    global local_db

    return jsonify(menu_item=local_db[menu_id].serialize)

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

        db["last_updated_time_stamp"] = int(sheet_time.cell(1, 1).value)
        last_updated_time_stamp = db["last_updated_time_stamp"]
        local_db = dict(db)

# end of full_update_local() ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


with shelve.open("database") as db:
    last_updated_time_stamp = db.get("last_updated_time_stamp", 0)
    local_db = dict(db)

if int(last_updated_time_stamp) < int(sheet_time.cell(1, 1).value) \
   or\
   int(sheet_time.cell(1, 1).value) == 0:

   full_update_local()


if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000)
