from flask import Flask, render_template, request
from pymongo import MongoClient
import pymysql
import joblib
import uuid

app = Flask(__name__)

# MongoDB connection
mongodb_uri = 'mongodb://localhost:27017/'  # Update with your actual MongoDB URI
try:
    mongo_client = MongoClient(mongodb_uri)
    mongo_db = mongo_client['admin']  # Change to 'admin' database
    mongo_collection = mongo_db['information']  # Collection name can be anything
    print("Connected to MongoDB")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# MySQL connection
mysql_conn = None
mysql_cursor = None
try:
    mysql_conn = pymysql.connect(
        host='127.0.0.1',
        user='root',  # Update with your MySQL username
        password='Sonr@98600',  # Update with your MySQL password
        database='testing',  # Update with your MySQL database name
        cursorclass=pymysql.cursors.DictCursor
    )
    mysql_cursor = mysql_conn.cursor()
    print("Connected to MySQL")

    # Create table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS backorder_predictions (
        id VARCHAR(255) PRIMARY KEY,
        national_inv FLOAT,
        lead_time FLOAT,
        sales_1_month FLOAT,
        pieces_past_due FLOAT,
        perf_6_month_avg FLOAT,
        in_transit_qty FLOAT,
        local_bo_qty FLOAT,
        deck_risk FLOAT,
        oe_constraint FLOAT,
        ppap_risk FLOAT,
        stop_auto_buy FLOAT,
        rev_stop FLOAT
    )
    """
    mysql_cursor.execute(create_table_query)
    mysql_conn.commit()
    print("Table 'backorder_predictions' ensured in MySQL")
except pymysql.MySQLError as err:
    print(f"Error: {err}")
except Exception as e:
    print(f"Error connecting to MySQL: {e}")

@app.route('/')
def home():
    return render_template('index.html')  # Serve the existing HTML file

@app.route('/form', methods=["POST"])
def brain():
    try:
        # Collect and convert data from form
        national_inv = float(request.form['national_inv'])
        lead_time = float(request.form['lead_time'])
        sales_1_month = float(request.form['sales_1_month'])
        pieces_past_due = float(request.form['pieces_past_due'])
        perf_6_month_avg = float(request.form['perf_6_month_avg'])
        in_transit_qty = float(request.form['in_transit_qty'])
        local_bo_qty = float(request.form['local_bo_qty'])
        deck_risk = float(request.form['deck_risk'])
        oe_constraint = float(request.form['oe_constraint'])
        ppap_risk = float(request.form['ppap_risk'])
        stop_auto_buy = float(request.form['stop_auto_buy'])
        rev_stop = float(request.form['rev_stop'])

        values = {
            "id": str(uuid.uuid4()),  # Ensure ID is a string
            "national_inv": national_inv,
            "lead_time": lead_time,
            "sales_1_month": sales_1_month,
            "pieces_past_due": pieces_past_due,
            "perf_6_month_avg": perf_6_month_avg,
            "in_transit_qty": in_transit_qty,
            "local_bo_qty": local_bo_qty,
            "deck_risk": deck_risk,
            "oe_constraint": oe_constraint,
            "ppap_risk": ppap_risk,
            "stop_auto_buy": stop_auto_buy,
            "rev_stop": rev_stop
        }

        # Insert data into MongoDB
        mongo_collection.insert_one(values)
        print("Data inserted into MongoDB")

        # Insert data into MySQL
        if mysql_conn and mysql_cursor:
            sql = """INSERT INTO backorder_predictions (
                     id, national_inv, lead_time, sales_1_month, pieces_past_due,
                     perf_6_month_avg, in_transit_qty, local_bo_qty, deck_risk,
                     oe_constraint, ppap_risk, stop_auto_buy, rev_stop)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            mysql_cursor.execute(sql, (
                values['id'], national_inv, lead_time, sales_1_month, pieces_past_due,
                perf_6_month_avg, in_transit_qty, local_bo_qty, deck_risk,
                oe_constraint, ppap_risk, stop_auto_buy, rev_stop
            ))
            mysql_conn.commit()
            print("Data inserted into MySQL")
        else:
            print("MySQL connection not established")

        # Predict using the machine learning model
        model = joblib.load(r'C:\Users\LP-182\Downloads\Backorder-Prediction-main\Backorder-Prediction-main\backorder_model')
        prediction = model.predict([[national_inv, lead_time, sales_1_month, pieces_past_due,
                                     perf_6_month_avg, in_transit_qty, local_bo_qty, deck_risk,
                                     oe_constraint, ppap_risk, stop_auto_buy, rev_stop]])

        result = "Product did not go on Backorder" if prediction[0] == 1 else "Product went on Backorder"
        return result
    except pymysql.MySQLError as e:
        print(f"SQL Error: {e}")
        return "An SQL error occurred"
    except Exception as e:
        print(f"General Error: {e}")
        return "An error occurred"

if __name__ == '__main__':
    app.run(debug=True, port=8080, threaded=True)
