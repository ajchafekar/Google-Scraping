# app.py
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import mysql.connector

app = Flask(__name__)

# MySQL database connection details
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",  # Enter your MySQL password here
    database="google_search_data",
    port=3306  # Default MySQL port
)

# Function to scrape Google search results
def scrape_google_search(query, num_results=10):
    base_url = f"https://www.google.com/search?q={query}&num={num_results}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing Google search results: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    search_results = []

    for result in soup.find_all("div", class_="tF2Cxc"):
        link = result.find("a")
        title = result.find("h3")
        snippet = result.find("span", class_="aCOpRe")

        if link and title:
            search_result = {
                "title": title.get_text(),
                "url": link["href"],
                "snippet": snippet.get_text() if snippet else ""
            }
            search_results.append(search_result)

    return search_results

# Function to create table in MySQL database and save data
def save_to_mysql(category, search_results):
    try:
        cursor = db_connection.cursor()

        # Create a table dynamically based on the category
        create_table_sql = f"CREATE TABLE IF NOT EXISTS `{category.lower().replace(' ', '_')}` (" \
                           "`id` INT AUTO_INCREMENT PRIMARY KEY," \
                           "`title` VARCHAR(255) NOT NULL," \
                           "`url` VARCHAR(255) NOT NULL," \
                           "`snippet` TEXT" \
                           ")"
        cursor.execute(create_table_sql)

        for result in search_results:
            sql = f"INSERT INTO `{category.lower().replace(' ', '_')}` (title, url, snippet) VALUES (%s, %s, %s)"
            values = (result["title"], result["url"], result["snippet"])
            cursor.execute(sql, values)

        db_connection.commit()
        cursor.close()

        print("Data saved successfully to MySQL database.")

    except mysql.connector.Error as e:
        print(f"Error saving data to MySQL database: {e}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scrape", methods=["POST"])
def scrape():
    category = request.form.get("category")
    num_results = int(request.form.get("num_results", 10))

    search_results = scrape_google_search(category, num_results)
    if search_results:
        save_to_mysql(category, search_results)
        return render_template("result.html", search_results=search_results)
    else:
        return jsonify({"success": False, "message": "Failed to scrape data."})

if __name__ == "__main__":
    app.run(debug=True)
