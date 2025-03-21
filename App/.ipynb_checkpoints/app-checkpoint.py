import streamlit as st
import pandas as pd
import random

# Load pre-clustered book data
@st.cache_data
def load_data():
    df = pd.read_csv("Book_Recommender_Final.csv")
    return df

df = load_data()

# --- App Layout ---
st.title("📚 Book Recommender")
st.subheader("Discover your next great read")

# --- User Inputs ---
name = st.text_input("What's your name?")
age = st.slider("How old is the reader?", 0, 80, 18)

if age < 8:
    st.write(f"Age: {age}, let's find some childrens books!")

elif 8 < age < 18:
    st.write(f"Age: {age}, finding books for adolescents and young adults!")

elif age > 18 :
    st.write(f"Age: {age}. Great, let's find some books!")

# Option to search or go random
use_lucky = st.checkbox("I'm feeling lucky (skip book selection)")

user_books = []
if not use_lucky:
    st.write("Select up to 5 of your favorite books")
    user_books = st.multiselect(
        "Start typing to search...",
        options=sorted(df['Title'].dropna().unique()),
        max_selections=5
    )

# --- Recommend Button ---
if st.button("Get Recommendations"):
    if use_lucky:
        # Randomly pick a cluster and return 10 high quality books from that cluster
        selected_cluster = random.choice(df['Cluster'].unique())
        recs = df[df['Cluster'] == selected_cluster]
    elif user_books:
        # Find the most common cluster among selected books
        selected_clusters = df[df['Title'].isin(user_books)]['Cluster']
        if selected_clusters.empty:
            st.warning("We couldn't match any of your books to our database.")
            st.stop()
        selected_cluster = selected_clusters.mode()[0]
        recs = df[df['Cluster'] == selected_cluster]
    else:
        st.warning("Please select your favorite books or choose 'I'm feeling lucky'.")
        st.stop()

    # Filter by age group
    age_filtered = recs[recs['Age_Group_Min'] <= age]
    age_filtered = age_filtered.sort_values(by='Quality_Score', ascending=False)

    # Remove selected books if applicable
    if user_books:
        age_filtered = age_filtered[~age_filtered['Title'].isin(user_books)]

    top_recs = age_filtered[['Title', 'Author', 'Genres', 'Quality_Score']].head(10)

    # --- Display Recommendations ---
    st.success(f"Here are your book recommendations, {name or 'reader'}:")
    st.table(top_recs.reset_index(drop=True))
