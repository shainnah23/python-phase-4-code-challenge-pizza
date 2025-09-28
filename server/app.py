#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os
from models import Restaurant, Pizza, RestaurantPizza, db
from sqlalchemy.exc import IntegrityError

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


def restaurant_shallow(r):
    return {'id': r.id, 'name': r.name, 'address': r.address}


def pizza_shallow(p):
    return {'id': p.id, 'name': p.name, 'ingredients': p.ingredients}


def restaurant_pizza_shallow(rp, include_nested=False):
    d = {'id': rp.id, 'price': rp.price, 'pizza_id': rp.pizza_id, 'restaurant_id': rp.restaurant_id}
    if include_nested:
        d['pizza'] = pizza_shallow(rp.pizza)
        d['restaurant'] = restaurant_shallow(rp.restaurant)
    return d


@app.route('/restaurants')
def get_restaurants():
    restaurants = Restaurant.query.all()
    result = [restaurant_shallow(r) for r in restaurants]
    return make_response(jsonify(result), 200)


@app.route('/restaurants/<int:id>')
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return make_response(jsonify({'error': 'Restaurant not found'}), 404)
    # include restaurant_pizzas
    rp_list = [restaurant_pizza_shallow(rp, include_nested=True) for rp in restaurant.restaurant_pizzas]
    data = restaurant_shallow(restaurant)
    data['restaurant_pizzas'] = rp_list
    return make_response(jsonify(data), 200)


@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return make_response(jsonify({'error': 'Restaurant not found'}), 404)
    db.session.delete(restaurant)
    db.session.commit()
    return ('', 204)


@app.route('/pizzas')
def get_pizzas():
    pizzas = Pizza.query.all()
    result = [pizza_shallow(p) for p in pizzas]
    return make_response(jsonify(result), 200)


@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()
    try:
        rp = RestaurantPizza(
            price=data.get('price'),
            pizza_id=data.get('pizza_id'),
            restaurant_id=data.get('restaurant_id')
        )
        db.session.add(rp)
        db.session.commit()
    except (ValueError, IntegrityError):
        db.session.rollback()
        return make_response(jsonify({'errors': ['validation errors']}), 400)

    result = restaurant_pizza_shallow(rp, include_nested=True)
    return make_response(jsonify(result), 201)


if __name__ == "__main__":
    app.run(port=5555, debug=True)
