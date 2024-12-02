from flask import Flask, request, render_template
import pandas as pd
import random
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load product and training data from CSV files
trending_products = pd.read_csv("models/trending_products.csv")
train_data = pd.read_csv("models/clean_data.csv")

# Configure database connection
app.secret_key = "alskdjfwoeieiurlskdjfslkdjf"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:@localhost/ecom"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Define database models for user signup and signin
class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Signin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)


# Function to truncate text to a specific length
def truncate(text, length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text


#content-based recommendations for a product
def content_based_recommendations(train_data, item_name, top_n=10):
    # Returns empty DataFrame if the product is not in the training data
    if item_name not in train_data['Name'].values:
        return pd.DataFrame()

    #TF-IDF vectorizer and calculate similarity scores
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix_content = tfidf_vectorizer.fit_transform(train_data['Tags'])
    cosine_similarities_content = cosine_similarity(tfidf_matrix_content, tfidf_matrix_content)

    # Fnding input product and sort similar items by similarity score
    item_index = train_data[train_data['Name'] == item_name].index[0]
    similar_items = list(enumerate(cosine_similarities_content[item_index]))
    similar_items = sorted(similar_items, key=lambda x: x[1], reverse=True)

    # Extract details of the top N similar products
    top_similar_items = similar_items[1:top_n + 1]
    recommended_item_indices = [x[0] for x in top_similar_items]
    recommended_items_details = train_data.iloc[recommended_item_indices][['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']]

    return recommended_items_details


#predefined random image URLs
random_image_urls = [
    "static/img_1.png",
    "static/img_2.png",
    "static/img_3.png",
    "static/img_4.png",
    "static/img_5.png",
    "static/img_6.png",
    "static/img_7.png",
    "static/img_8.png",
]


@app.route("/")
def index():
    # Random image URLs and prices for the trending products
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template(
        'index.html',
        trending_products=trending_products.head(8),
        truncate=truncate,
        random_product_image_urls=random_product_image_urls,
        random_price=random.choice(price)
    )


@app.route("/main")
def main():
    #main page with an empty recommendations DataFrame by default
    return render_template('main.html', content_based_rec=pd.DataFrame())


@app.route("/index")
def indexredirect():
    #load trending products
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template(
        'index.html',
        trending_products=trending_products.head(8),
        truncate=truncate,
        random_product_image_urls=random_product_image_urls,
        random_price=random.choice(price)
    )


@app.route("/signup", methods=['POST', 'GET'])
def signup():
    # Handle signup form submission
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        new_signup = Signup(username=username, email=email, password=password)
        db.session.add(new_signup)
        db.session.commit()

    return index()


@app.route('/signin', methods=['POST', 'GET'])
def signin():
    # Handle signin form submission
    if request.method == 'POST':
        username = request.form['signinUsername']
        password = request.form['signinPassword']
        new_signup = Signin(username=username, password=password)
        db.session.add(new_signup)
        db.session.commit()

    return index()


@app.route("/recommendations", methods=['POST', 'GET'])
def recommendations():
    #product recommendation requests
    if request.method == 'POST':
        prod = request.form.get('prod')
        nbr = int(request.form.get('nbr', 10))
        content_based_rec = content_based_recommendations(train_data, prod, top_n=nbr)

        # Display message if no recommendations are available
        if content_based_rec.empty:
            message = "No recommendations available for this product."
            return render_template('main.html', message=message, content_based_rec=pd.DataFrame())
        else:
            return render_template(
                'main.html',
                content_based_rec=content_based_rec,
                truncate=truncate
            )


if __name__ == '__main__':
    app.run(debug=True)
