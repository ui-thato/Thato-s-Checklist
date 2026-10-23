LOAD_RAW = '''# Start the cleaning from the saved raw file, so this part can be re-run
# without scraping the website again
books = pd.read_csv("books_raw.csv")
print(books.shape)
books.info()'''

CHECK_RAW = '''print("Missing values in each column:")
print(books.isnull().sum())

print("\\nExamples of the raw text we need to clean:")
print(repr(books.loc[0, "price_raw"]))
print(repr(books.loc[0, "availability_raw"]))
print(repr(books.loc[0, "availability_detail"]))
print(books["rating_raw"].unique())'''

DUPLICATES = '''# Exact duplicate rows (the same book scraped twice)
print("Exact duplicate rows:", books.duplicated().sum())

# The book page URL is unique for every product, so it is the safest way to spot repeats
print("Repeated book URLs:", books["book_url"].duplicated().sum())

# Some different books can share the same title, so I check titles separately
repeated_titles = books[books["title"].duplicated(keep=False)].sort_values("title")
print("Rows that share a title with another row:", len(repeated_titles))
repeated_titles[["title", "category", "price_raw", "upc"]]'''

DROP_DUPS = '''rows_before = len(books)
books = books.drop_duplicates(subset="book_url").reset_index(drop=True)
print("Rows removed:", rows_before - len(books))
print("Rows left:", len(books))'''

CLEAN_PRICE = '''def clean_price(price_text):
    """Turn text like '£51.77' (or a badly encoded 'Â£51.77') into the number 51.77."""
    if pd.isnull(price_text):
        return np.nan
    # Keep only digits and the decimal point
    number_text = re.sub(r"[^0-9.]", "", str(price_text))
    if number_text == "":
        return np.nan
    return float(number_text)


books["price_gbp"] = books["price_raw"].apply(clean_price)
books[["price_raw", "price_gbp"]].head()'''

CLEAN_RATING = '''# A dictionary that maps the rating words to numbers
rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

books["rating"] = books["rating_raw"].str.strip().str.title().map(rating_map)

print("Ratings that could not be converted:", books["rating"].isnull().sum())
books[["rating_raw", "rating"]].drop_duplicates().sort_values("rating")'''

CLEAN_STOCK = '''def get_stock_quantity(availability_text):
    """Find the number in text like 'In stock (22 available)'. Returns NaN if there is none."""
    if pd.isnull(availability_text):
        return np.nan
    match = re.search(r"(\\d+) available", str(availability_text))
    if match:
        return int(match.group(1))
    return np.nan


# Stock status from the listing page, e.g. "In stock"
books["stock_status"] = books["availability_raw"].str.strip()
books["in_stock"] = (books["stock_status"] == "In stock").astype(int)

# Stock quantity from the book's own page, e.g. "In stock (22 available)"
if "availability_detail" in books.columns:
    books["stock_quantity"] = books["availability_detail"].apply(get_stock_quantity)
else:
    books["stock_quantity"] = np.nan

books[["availability_raw", "stock_status", "in_stock", "stock_quantity"]].head()'''

CLEAN_TEXT = '''# Titles and categories: remove extra spaces at the start/end and inside the text
books["title"] = books["title"].str.strip().str.replace(r"\\s+", " ", regex=True)
books["category"] = books["category"].str.strip()

# Descriptions: some books have none, and many end with "...more"
books["description"] = (books["description"].fillna("")
                        .str.replace("...more", "", regex=False)
                        .str.replace(r"\\s+", " ", regex=True)
                        .str.strip())

# Simple numeric features made from the text fields
books["title_length"] = books["title"].str.split().str.len()           # words in the title
books["description_length"] = books["description"].str.split().str.len()  # words in the description
books["has_description"] = (books["description_length"] > 0).astype(int)

# Number of reviews comes through as text, so turn it into a number
books["num_reviews"] = pd.to_numeric(books["num_reviews_raw"], errors="coerce")

print("Books with no description:", (books["has_description"] == 0).sum())
print("Different review counts found:", books["num_reviews"].unique())'''

MISSING = '''print("Missing values after cleaning:")
print(books[["title", "price_gbp", "rating", "stock_status", "stock_quantity", "category"]].isnull().sum())'''

MISSING_FIX = '''# Rows without a usable price or rating can't be analysed, so they are removed.
rows_before = len(books)
books = books.dropna(subset=["price_gbp", "rating"])
print("Rows removed for missing price or rating:", rows_before - len(books))

# If a book page failed to load, its stock quantity is missing.
# I fill it with the median so one failed page doesn't remove the whole book.
missing_quantity = books["stock_quantity"].isnull().sum()
if missing_quantity > 0:
    books["stock_quantity"] = books["stock_quantity"].fillna(books["stock_quantity"].median())
print("Stock quantities filled with the median:", missing_quantity)

# Store whole numbers as integers
books["rating"] = books["rating"].astype(int)
books["stock_quantity"] = books["stock_quantity"].astype(int)'''

SAVE_CLEAN = '''clean_columns = ["upc", "title", "category", "price_gbp", "rating", "stock_status",
                 "in_stock", "stock_quantity", "num_reviews", "title_length",
                 "description_length", "has_description", "description", "book_url"]

books_clean = books[clean_columns].reset_index(drop=True)
books_clean.to_csv("books_clean.csv", index=False)

print("Saved books_clean.csv")
print("Shape (rows, columns):", books_clean.shape)
books_clean.head()'''

DESCRIBE = '''books_clean.info()
books_clean[["price_gbp", "rating", "stock_quantity", "title_length", "description_length"]].describe().round(2)'''

PLOT_PRICE = '''plt.hist(books_clean["price_gbp"], bins=30, color="steelblue", edgecolor="white")
plt.axvline(books_clean["price_gbp"].mean(), color="red", linestyle="--",
            label=f"Mean = £{books_clean['price_gbp'].mean():.2f}")
plt.axvline(books_clean["price_gbp"].median(), color="orange", linestyle="--",
            label=f"Median = £{books_clean['price_gbp'].median():.2f}")
plt.title("Figure 1: Distribution of book prices")
plt.xlabel("Price (GBP)")
plt.ylabel("Number of books")
plt.legend()
plt.show()'''

PLOT_RATING_COUNT = '''rating_counts = books_clean["rating"].value_counts().sort_index()

plt.bar(rating_counts.index, rating_counts.values, color="seagreen")
for rating, count in rating_counts.items():
    plt.text(rating, count + 5, str(count), ha="center")
plt.title("Figure 2: Number of books at each star rating")
plt.xlabel("Star rating")
plt.ylabel("Number of books")
plt.xticks([1, 2, 3, 4, 5])
plt.show()'''

PLOT_PRICE_RATING = '''average_by_rating = books_clean.groupby("rating")["price_gbp"].mean()
print(average_by_rating.round(2))

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Left: average price for each rating
axes[0].bar(average_by_rating.index, average_by_rating.values, color="darkorange")
for rating, price in average_by_rating.items():
    axes[0].text(rating, price + 0.5, f"£{price:.2f}", ha="center")
axes[0].set_title("Figure 3a: Average price by star rating")
axes[0].set_xlabel("Star rating")
axes[0].set_ylabel("Average price (GBP)")
axes[0].set_ylim(0, 45)

# Right: box plot showing the full spread of prices for each rating
sns.boxplot(data=books_clean, x="rating", y="price_gbp", hue="rating",
            palette="Oranges", legend=False, ax=axes[1])
axes[1].set_title("Figure 3b: Spread of prices by star rating")
axes[1].set_xlabel("Star rating")
axes[1].set_ylabel("Price (GBP)")

plt.tight_layout()
plt.show()'''

PLOT_GENRE_COUNT = '''genre_counts = books_clean["category"].value_counts()
print("Number of genres:", len(genre_counts))

top_genres = genre_counts.head(15).sort_values()
plt.figure(figsize=(9, 6))
plt.barh(top_genres.index, top_genres.values, color="slateblue")
plt.title("Figure 4: The 15 genres with the most books")
plt.xlabel("Number of books")
plt.show()'''

PLOT_GENRE_PRICE = '''# Only genres with at least 10 books, so one or two books don't give a misleading average
genre_summary = (books_clean.groupby("category")
                 .agg(books=("title", "count"), average_price=("price_gbp", "mean"),
                      average_rating=("rating", "mean"))
                 .query("books >= 10")
                 .sort_values("average_price"))
print("Genres with at least 10 books:", len(genre_summary))

plt.figure(figsize=(9, 8))
colours = ["indianred" if price > books_clean["price_gbp"].mean() else "steelblue"
           for price in genre_summary["average_price"]]
plt.barh(genre_summary.index, genre_summary["average_price"], color=colours)
plt.axvline(books_clean["price_gbp"].mean(), color="black", linestyle="--",
            label="Average for whole catalogue")
plt.title("Figure 5: Average price by genre (genres with 10+ books)")
plt.xlabel("Average price (GBP)")
plt.legend()
plt.show()

genre_summary.round(2)'''

PLOT_STOCK = '''fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Left: stock status counts
status_counts = books_clean["stock_status"].value_counts()
axes[0].bar(status_counts.index, status_counts.values, color="teal")
axes[0].set_title("Figure 6a: Stock status")
axes[0].set_ylabel("Number of books")

# Right: how many copies are in stock
axes[1].hist(books_clean["stock_quantity"], bins=range(0, books_clean["stock_quantity"].max() + 2),
             color="teal", edgecolor="white")
axes[1].set_title("Figure 6b: Number of copies in stock")
axes[1].set_xlabel("Copies available")
axes[1].set_ylabel("Number of books")

plt.tight_layout()
plt.show()

print(status_counts)'''

PLOT_SCATTER = '''fig, axes = plt.subplots(1, 2, figsize=(13, 5))

sns.regplot(data=books_clean, x="stock_quantity", y="price_gbp", ax=axes[0],
            scatter_kws={"alpha": 0.3}, line_kws={"color": "red"})
axes[0].set_title("Figure 7a: Price vs copies in stock")
axes[0].set_xlabel("Copies in stock")
axes[0].set_ylabel("Price (GBP)")

sns.regplot(data=books_clean, x="description_length", y="price_gbp", ax=axes[1],
            scatter_kws={"alpha": 0.3}, line_kws={"color": "red"})
axes[1].set_title("Figure 7b: Price vs description length")
axes[1].set_xlabel("Words in description")
axes[1].set_ylabel("Price (GBP)")

plt.tight_layout()
plt.show()'''

PLOT_CORR = '''numeric_columns = ["price_gbp", "rating", "stock_quantity", "title_length", "description_length"]
correlations = books_clean[numeric_columns].corr()

plt.figure(figsize=(7, 5.5))
sns.heatmap(correlations, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1)
plt.title("Figure 8: Correlation between the numeric variables")
plt.show()

print("Correlation of each variable with price:")
print(correlations["price_gbp"].drop("price_gbp").round(3))'''

MODEL_DATA = '''# Numeric features
numeric_features = ["rating", "stock_quantity", "title_length", "description_length"]

# Genre is text, so it is turned into 0/1 "dummy" columns.
# Small genres (under 10 books) are grouped as "Other" so each dummy column has enough books.
genre_counts = books_clean["category"].value_counts()
large_genres = genre_counts[genre_counts >= 10].index
books_clean["genre_group"] = books_clean["category"].where(
    books_clean["category"].isin(large_genres), "Other")

# drop_first=True leaves out one genre to act as the baseline
genre_dummies = pd.get_dummies(books_clean["genre_group"], prefix="genre",
                               drop_first=True, dtype=int)

X = pd.concat([books_clean[numeric_features], genre_dummies], axis=1)
y = books_clean["price_gbp"]

print("Feature table shape:", X.shape)
print("Baseline genre (left out):", sorted(books_clean["genre_group"].unique())[0])
X.head()'''

SPLIT = '''X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training rows:", len(X_train))
print("Testing rows: ", len(X_test))'''

EVAL_FUNC = '''def evaluate(name, actual, predicted):
    """Work out the four evaluation metrics and return them in a dictionary."""
    mse = mean_squared_error(actual, predicted)
    return {"model": name,
            "MAE": mean_absolute_error(actual, predicted),
            "MSE": mse,
            "RMSE": np.sqrt(mse),
            "R2": r2_score(actual, predicted)}'''

BASELINE = '''# Baseline: always guess the average training price.
# A useful model should beat this.
baseline_predictions = np.full(len(y_test), y_train.mean())
results = [evaluate("Baseline (always predict mean)", y_test, baseline_predictions)]
print(f"Baseline guess for every book: £{y_train.mean():.2f}")'''

MODEL_SIMPLE = '''# Model 1: simple linear regression with one feature (star rating)
simple_model = LinearRegression()
simple_model.fit(X_train[["rating"]], y_train)
simple_predictions = simple_model.predict(X_test[["rating"]])

print(f"Price = {simple_model.intercept_:.2f} + ({simple_model.coef_[0]:.2f} x rating)")
results.append(evaluate("Model 1: rating only", y_test, simple_predictions))'''

MODEL_MULTI = '''# Model 2: multiple linear regression with all the features
multi_model = LinearRegression()
multi_model.fit(X_train, y_train)
multi_predictions = multi_model.predict(X_test)

results.append(evaluate("Model 2: all features", y_test, multi_predictions))

# Training score as well, to check for overfitting
train_r2 = r2_score(y_train, multi_model.predict(X_train))
print(f"Model 2 R² on the training data: {train_r2:.3f}")'''

RESULTS = '''results_table = pd.DataFrame(results).set_index("model").round(3)
results_table'''

COEFS = '''coefficients = pd.DataFrame({"feature": X.columns, "coefficient": multi_model.coef_})
print(f"Intercept (β₀): {multi_model.intercept_:.2f}")
coefficients.sort_values("coefficient").round(3)'''

PLOT_PRED = '''fig, axes = plt.subplots(1, 2, figsize=(13, 5))

axes[0].scatter(y_test, multi_predictions, alpha=0.5)
axes[0].plot([10, 60], [10, 60], color="red", linestyle="--", label="Perfect prediction")
axes[0].set_title("Figure 9a: Actual vs predicted price (test set)")
axes[0].set_xlabel("Actual price (GBP)")
axes[0].set_ylabel("Predicted price (GBP)")
axes[0].legend()

residuals = y_test - multi_predictions
axes[1].hist(residuals, bins=25, color="grey", edgecolor="white")
axes[1].axvline(0, color="red", linestyle="--")
axes[1].set_title("Figure 9b: Prediction errors (residuals)")
axes[1].set_xlabel("Actual minus predicted price (GBP)")
axes[1].set_ylabel("Number of books")

plt.tight_layout()
plt.show()'''
