
import streamlit as st
import pandas as pd
import random
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = st.secrets["GOOGLE_BOOKS_API_KEY"]
READLIST_FILE = "App/user_list.csv"

st.code(response.url)


def fetch_book_info(title, api_key=None):
    params = {
        'q': title,
        'maxResults': 1,
        'printType': 'books',
        'langRestrict': 'en'
    }
    if api_key:
        params['key'] = api_key

    try:
        response = requests.get('https://www.googleapis.com/books/v1/volumes', params=params, timeout=5)
        if response.status_code != 200:
            st.warning(f"API Error: {response.status_code}")
            return None, "No description available."

        data = response.json()
        if 'items' not in data:
            st.info(f"No items returned for title: {title}")
            return None, "No description available."

        item = data['items'][0]['volumeInfo']
        thumbnail = item.get('imageLinks', {}).get('thumbnail')
        description = item.get('description', 'No description available.')
        return thumbnail, description

    except Exception as e:
        st.error(f"API fetch error: {e}")
        return None, "No description available."

@st.cache_data
def load_data():
    return pd.read_csv("App/Book_Recommender_Final.csv")

def save_to_csv(title, status):
    entry = pd.DataFrame([[title, status]], columns=["Title", "Status"])
    if os.path.exists(READLIST_FILE):
        entry.to_csv(READLIST_FILE, mode='a', header=False, index=False)
    else:
        entry.to_csv(READLIST_FILE, index=False)

def render_badges(items):
    return " ".join([f"`{item}`" for item in items])

def generate_recommendations():
            if selected_method == "lucky":
                selected_cluster = random.choice(df['Cluster'].unique())
                recs = df[df['Cluster'] == selected_cluster]
            elif selected_method == "books":
                selected_clusters = df[df['Title'].isin(user_books)]['Cluster']
                if selected_clusters.empty:
                    st.warning("We couldn't match any of your books to our database.")
                    st.stop()
                selected_cluster = selected_clusters.mode()[0]
                recs = df[df['Cluster'] == selected_cluster]
            elif selected_method == "authors":
                selected_clusters = df[df['Author'].isin(user_authors)]['Cluster']
                if selected_clusters.empty:
                    st.warning("We couldn't match any of your books to our database.")
                    st.stop()
                selected_cluster = selected_clusters.mode()[0]
                recs = df[df['Cluster'] == selected_cluster]
            elif selected_method == "genres":
                genre_mask = df['Genres'].dropna().apply(lambda g: any(genre in g for genre in user_genres))
                recs = df[genre_mask]
            else:
                st.warning("Please select a recommendation method.")
                st.stop()

            age_filtered = recs[recs['Age_Group_Min'] <= age]
            age_filtered = age_filtered.sort_values(by='Quality_Score', ascending=False)

            if selected_method == "books":
                age_filtered = age_filtered[~age_filtered['Title'].isin(user_books)]

            return age_filtered.sample(n=min(10, len(age_filtered)), random_state=st.session_state['rec_seed'])

df = load_data()
st.title("📚 BookRec")
st.subheader("Discover your next great read")

st.markdown("---")

# Step 1: Name and Age
st.markdown("### Step 1️⃣")
st.markdown("##### Reader info")
name = st.text_input("Name")
age = 0
if name:
    age = st.number_input("Reader age", min_value=0, step=1)

    st.markdown("---")

# Step 2: Choose recommendation method
user_books = []
user_genres = []
user_authors = []
selected_method = None

if name is not None and age > 0:
    st.markdown("### Step 2️⃣")
    st.markdown("##### Reading preferences")
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Favourite Books", "✏️ Favourite Authors", "🎭 Favourite Genres", "🍀 Surprise Me"])

    with tab1:
        user_books = st.multiselect(
            "Select up to 3 of your favourite books:",
            options=df['Title'].dropna().unique(),
            max_selections=3
        )
        if user_books:
            selected_method = "books"

    with tab2:
        user_authors = st.multiselect(
            "Select up to 3 of your favourite authors:",
            options=df['Author'].dropna().unique(),
            max_selections=3
        )
        if user_authors:
            selected_method = "authors"

    with tab3:
        all_genres = ['Young Adult', 'Fiction', 'Fantasy','Science Fiction','Historical Fiction','Historical','Adventure','Romance','Paranormal','Contemporary','Classics','Mystery','Thriller','Crime','Mystery Thriller','Suspense','Horror','Science','Juvenile Fiction','Philosophy','Short Stories','Graphic Novels','Feminism','Humor','Drama','Children','Greek Mythology','Nonfiction','Detective','Contemporary']
        user_genres = st.multiselect(
            "Select up to 3 of your favourite genres:",
            options=all_genres,
            max_selections=3
        )
        if user_genres:
            selected_method = "genres"


    with tab4:
        lucky_click = st.checkbox("Surprise me!")
        if lucky_click:
            selected_method = "lucky"

    st.markdown("---")

if selected_method in ["books", "authors", "genres", "lucky"]:
    st.markdown("### Step 3️⃣")
    st.markdown("##### Get recommendations")

    # 👤 Reader info
    if 0 < age < 8:
        st.info(f"**👤 Reader:** {name}, {age} years old - child")

    elif 8 < age < 18:
        st.info(f"**👤 Reader:** {name}, {age} years old - young adult")

    elif age > 18 :
        st.info(f"**👤 Reader:** {name}, {age} years old - adult")

    # 🏷️ Preferences
    if selected_method == "lucky" and not any([user_books, user_authors, user_genres]):
        st.success("🍀 Surprise Me Mode enabled — we’ll pick something random!")

    if user_books:
        st.markdown(f"**📚 Favourite Books:** {render_badges(user_books)}")

    if user_authors:
        st.markdown(f"**✏️ Favourite Authors:** {render_badges(user_authors)}")

    if user_genres:
        st.markdown(f"**🎭 Favourite Genres:** {render_badges(user_genres)}")

    if st.button("🔎 Generate"):
        if 'rec_seed' not in st.session_state:
            st.session_state['rec_seed'] = random.randint(1, 10000)
        st.session_state['recommendations'] = generate_recommendations()

# Step 4: Display results with options to get more or download
if 'recommendations' in st.session_state and st.session_state['recommendations'] is not None:
    st.success(f"Here are your book recommendations, {name}:")

    for _, row in st.session_state['recommendations'].iterrows():
        title = row['Title']
        author = row.get('Author')
        score = row['Quality_Score']
        genres = row['Genres']
        pages = row.get('Page_Number', None)
        rating = row.get('Avg_Rating', None)
        popularity = row.get('Num_Ratings', None)

        thumbnail, description = fetch_book_info(title, api_key=API_KEY)

        short_desc = (description[:150].rsplit(' ', 1)[0] + "...") if len(description) > 300 else description
        score_percentage = int(score * 100)

        cols = st.columns([1, 3])
        with cols[0]:
            if thumbnail:
                st.image(thumbnail, width=100)
            else:
                st.write("No cover")

        with cols[1]:
            st.markdown(f"### {title}")
            st.markdown(f"###### ✏️ {author}")
            if pd.notna(rating):
                st.markdown(f"🌟 **Avg. Rating**: {round(rating, 2)}")
            if pd.notna(popularity):
                st.markdown(f"👥 **# of Ratings**: {int(popularity)}")
            st.markdown(f"🎭 **Genres**: {genres}")
            if pd.notna(pages):
                st.markdown(f"📖 **Pages**: {int(pages)}")
            st.markdown(f"**Description**: {short_desc}")
            if description != short_desc:
                with st.expander("Show full description"):
                    st.write(description)

            action_cols = st.columns([1, 1])

            with action_cols[0]:
                if st.button("📌 Add to Reading List", key=f"want_{title}"):
                    save_to_csv(title, "Want to Read")
                    st.info(f"Added '{title}' to your reading list.")

        st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Get More Recommendations"):
            st.session_state['rec_seed'] += 1
            st.session_state['recommendations'] = generate_recommendations()
    with col2:
        with open(READLIST_FILE, "rb") as f:
            data_to_download = f.read()

            st.download_button(
            label="⬇️ Download My Read List",
            data=data_to_download,
            file_name="user_list.csv",
            mime="text/csv"
)


