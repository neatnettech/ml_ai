# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Module 9.1 — NLP & Text Processing
#
# Natural Language Processing (NLP) is a branch of AI that helps computers
# understand, interpret, and generate human language. From spam filters to
# chatbots to search engines, NLP is everywhere.
#
# **What you'll learn:**
# - How to convert text into numbers that ML models can use
# - Text preprocessing techniques (tokenization, stemming, etc.)
# - Bag of Words and TF-IDF representations
# - Building a text classifier (sentiment analysis)
# - Introduction to word embeddings and transformers

# %%
import numpy as np
import matplotlib.pyplot as plt
import re
from collections import Counter

# sklearn imports
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline

print("All imports successful!")

# %% [markdown]
# ---
# ## 1. Text as Data
#
# Machine learning models work with **numbers** — vectors, matrices, tensors.
# But text is made of characters and words. So the fundamental question in NLP is:
#
# > **How do we convert text into numbers?**
#
# This is called **text representation** or **feature extraction**, and there are
# many approaches, from simple counting to sophisticated neural embeddings.
#
# Let's start with the simplest ideas and work our way up.

# %%
# The most naive approach: assign a number to each character
text = "hello"
as_numbers = [ord(c) for c in text]  # ASCII codes
print(f"'{text}' as ASCII codes: {as_numbers}")

# But this doesn't capture meaning!
# 'hello' and 'olleh' would have the same set of numbers
# 'good' and 'great' would look completely different despite similar meaning

# We need smarter approaches...

# %%
# A better idea: represent text by which WORDS appear
# This is the foundation of Bag of Words (we'll formalize it in Section 3)

doc1 = "I love this movie"
doc2 = "I hate this movie"
doc3 = "This movie is great I love it"

# Even just counting words tells us something:
for doc in [doc1, doc2, doc3]:
    words = doc.lower().split()
    print(f"'{doc}' -> {dict(Counter(words))}")

# %% [markdown]
# ---
# ## 2. Text Preprocessing
#
# Before we can convert text to numbers, we need to **clean and normalize** it.
# Raw text is messy: different cases, punctuation, irrelevant words, etc.
#
# The main preprocessing steps are:
# 1. **Lowercasing** — "The" and "the" should be treated the same
# 2. **Removing punctuation** — "great!" and "great" are the same word
# 3. **Tokenization** — splitting text into individual words (tokens)
# 4. **Stop word removal** — removing common words like "the", "is", "and"
# 5. **Stemming / Lemmatization** — reducing words to their root form

# %% [markdown]
# ### 2.1 Lowercasing and Removing Punctuation

# %%
text = "NLP is Amazing! It's used in search engines, chatbots, and MORE."

# Step 1: Lowercase
text_lower = text.lower()
print("Lowercased:", text_lower)

# Step 2: Remove punctuation using regex
# re.sub replaces everything that's NOT a letter, number, or space
text_clean = re.sub(r'[^a-z0-9\s]', '', text_lower)
print("No punctuation:", text_clean)

# %% [markdown]
# ### 2.2 Tokenization

# %%
# Tokenization = splitting text into individual words (tokens)
text = "Natural language processing is fascinating"

# Simple approach: split on whitespace
tokens = text.lower().split()
print("Tokens:", tokens)
print("Number of tokens:", len(tokens))

# For more complex text, regex tokenization is better
text2 = "It's a well-known fact: NLP is #1!"
tokens_simple = text2.lower().split()
tokens_regex = re.findall(r'[a-z]+', text2.lower())

print("\nSimple split:", tokens_simple)  # keeps punctuation attached
print("Regex split: ", tokens_regex)      # cleaner tokens

# %% [markdown]
# ### 2.3 Stop Word Removal
#
# Stop words are extremely common words ("the", "is", "and", "a", ...) that
# usually don't carry much meaning. Removing them reduces noise and lets
# the model focus on the words that actually matter.

# %%
# A simple stop word list (sklearn has a built-in one too)
STOP_WORDS = {
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'she', 'it',
    'they', 'them', 'this', 'that', 'is', 'are', 'was', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'could', 'should', 'may', 'might', 'shall', 'can',
    'a', 'an', 'the', 'and', 'but', 'or', 'if', 'so', 'as', 'at',
    'by', 'for', 'in', 'of', 'on', 'to', 'up', 'with', 'from',
    'not', 'no', 'nor', 'very', 'too', 'just', 'about'
}

text = "This movie is not very good and the acting was terrible"
tokens = text.lower().split()
filtered = [w for w in tokens if w not in STOP_WORDS]

print("Original tokens:", tokens)
print("After stop word removal:", filtered)
print(f"Removed {len(tokens) - len(filtered)} stop words")

# Note: be careful! Removing 'not' changes meaning.
# In sentiment analysis, you might want to keep negation words.

# %% [markdown]
# ### 2.4 Stemming and Lemmatization
#
# These reduce words to a base or root form so that variations are treated
# as the same word:
#
# - **Stemming**: Chops off word endings using rules (fast but crude).
#   - "running" -> "run", "better" -> "better", "studies" -> "studi"
# - **Lemmatization**: Uses vocabulary and grammar to find the true root (slower but accurate).
#   - "running" -> "run", "better" -> "good", "studies" -> "study"
#
# We'll implement a simple stemmer here. Libraries like NLTK or spaCy
# provide more robust implementations.

# %%
# A very simple suffix-stripping stemmer
def simple_stem(word):
    """Remove common English suffixes."""
    suffixes = ['ing', 'ed', 'ly', 'es', 's', 'ment', 'ness', 'tion']
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[:-len(suffix)]
    return word

# Test it
words = ['running', 'walked', 'happily', 'studies', 'boxes',
         'movement', 'darkness', 'playing', 'education']

for w in words:
    print(f"  {w:15s} -> {simple_stem(w)}")

print("\nNote: This simple stemmer is imperfect!")
print("  'better' ->", simple_stem('better'), "(should be 'good' with lemmatization)")


# %% [markdown]
# ### 2.5 Putting It Together: A Preprocessing Pipeline

# %%
def preprocess_text(text, remove_stopwords=True, stem=False):
    """Full text preprocessing pipeline.
    
    Steps:
      1. Lowercase
      2. Remove punctuation
      3. Tokenize
      4. Optionally remove stop words
      5. Optionally stem
    
    Returns a cleaned string.
    """
    # 1. Lowercase
    text = text.lower()
    
    # 2. Remove punctuation (keep only letters and spaces)
    text = re.sub(r'[^a-z\s]', '', text)
    
    # 3. Tokenize
    tokens = text.split()
    
    # 4. Remove stop words
    if remove_stopwords:
        tokens = [w for w in tokens if w not in STOP_WORDS]
    
    # 5. Stemming
    if stem:
        tokens = [simple_stem(w) for w in tokens]
    
    return ' '.join(tokens)


# Demo
sample = "The actors were AMAZING! I loved the special effects, and the story was great."
print("Original:    ", sample)
print("Preprocessed:", preprocess_text(sample))
print("With stemming:", preprocess_text(sample, stem=True))

# %% [markdown]
# ---
# ## 3. Bag of Words (BoW)
#
# The **Bag of Words** model is one of the simplest ways to represent text as numbers.
#
# The idea:
# 1. Build a **vocabulary** — a list of all unique words across all documents.
# 2. Represent each document as a **vector** where each element counts how many
#    times a vocabulary word appears in that document.
#
# It's called "bag" of words because we throw away word **order** — we only care
# about which words appear and how often.

# %%
# Let's build BoW from scratch first to understand it
documents = [
    "I love this movie",
    "This movie is terrible",
    "Great movie I love it",
    "Terrible acting terrible script"
]

# Step 1: Build vocabulary
all_words = set()
for doc in documents:
    for word in doc.lower().split():
        all_words.add(word)

vocab = sorted(all_words)  # sorted for consistency
print("Vocabulary:", vocab)
print(f"Vocabulary size: {len(vocab)} words\n")

# Step 2: Create document-term matrix
word_to_idx = {word: i for i, word in enumerate(vocab)}

bow_matrix = np.zeros((len(documents), len(vocab)), dtype=int)
for doc_idx, doc in enumerate(documents):
    for word in doc.lower().split():
        bow_matrix[doc_idx, word_to_idx[word]] += 1

print("Document-Term Matrix:")
print(f"{'':30s}", '  '.join(f"{w:>8s}" for w in vocab))
for i, doc in enumerate(documents):
    print(f"{doc:30s}", '  '.join(f"{v:8d}" for v in bow_matrix[i]))

# %% [markdown]
# ### 3.1 CountVectorizer from sklearn
#
# Sklearn's `CountVectorizer` does all of this automatically — and handles
# many edge cases we'd have to code ourselves.

# %%
documents = [
    "I love this movie",
    "This movie is terrible",
    "Great movie I love it",
    "Terrible acting terrible script"
]

# Create the vectorizer and fit on documents
count_vec = CountVectorizer()
bow_matrix = count_vec.fit_transform(documents)

# Vocabulary
print("Vocabulary:", count_vec.get_feature_names_out())
print(f"\nShape: {bow_matrix.shape}  (4 documents x {bow_matrix.shape[1]} words)")

# The result is a sparse matrix — convert to dense for display
print("\nDocument-Term Matrix (dense):")
dense = bow_matrix.toarray()
for i, doc in enumerate(documents):
    print(f"  Doc {i}: {dense[i]}  <- '{doc}'")

# %%
# Visualize the document-term matrix as a heatmap
feature_names = count_vec.get_feature_names_out()

fig, ax = plt.subplots(figsize=(10, 3))
im = ax.imshow(dense, cmap='Blues', aspect='auto')
ax.set_xticks(range(len(feature_names)))
ax.set_xticklabels(feature_names, rotation=45, ha='right')
ax.set_yticks(range(len(documents)))
ax.set_yticklabels([f"Doc {i}" for i in range(len(documents))])
ax.set_title("Bag of Words: Document-Term Matrix")

# Add count values in cells
for i in range(dense.shape[0]):
    for j in range(dense.shape[1]):
        ax.text(j, i, str(dense[i, j]), ha='center', va='center', fontsize=10)

plt.colorbar(im, label='Word Count')
plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# ## 4. TF-IDF
#
# ### The Problem with Bag of Words
#
# In BoW, every word is treated equally. But some words like "the", "is", "movie"
# appear in almost every document and are not very informative. Meanwhile, rare
# words like "excellent" or "terrible" carry much more meaning.
#
# **TF-IDF** (Term Frequency - Inverse Document Frequency) solves this by
# **down-weighting common words** and **up-weighting rare, informative words**.
#
# The formula:
#
# $$\text{TF-IDF}(t, d) = \text{TF}(t, d) \times \text{IDF}(t)$$
#
# - **TF(t, d)** = how often term *t* appears in document *d* (same as BoW count)
# - **IDF(t)** = log(total documents / documents containing *t*) — rare words get higher IDF

# %%
# Let's see how IDF works with a concrete example
documents = [
    "the movie was great and the acting was superb",
    "the movie was terrible and the plot was awful",
    "great acting and wonderful storyline",
    "awful movie terrible acting"
]
n_docs = len(documents)

# Count how many documents each word appears in
word_doc_count = Counter()
for doc in documents:
    unique_words = set(doc.lower().split())
    for word in unique_words:
        word_doc_count[word] += 1

print("Word -> appears in N docs -> IDF score")
print("-" * 50)
for word, count in sorted(word_doc_count.items()):
    idf = np.log(n_docs / count)
    label = "<-- common (low IDF)" if idf < 0.5 else ""
    print(f"  {word:15s}  {count} docs   IDF = {idf:.3f}  {label}")

# %%
# TF-IDF with sklearn
tfidf_vec = TfidfVectorizer()
tfidf_matrix = tfidf_vec.fit_transform(documents)

feature_names = tfidf_vec.get_feature_names_out()
tfidf_dense = tfidf_matrix.toarray()

print("TF-IDF Matrix (values are weighted, not raw counts):")
print(f"{'':50s}", '  '.join(f"{w:>8s}" for w in feature_names))
for i, doc in enumerate(documents):
    vals = '  '.join(f"{v:8.3f}" for v in tfidf_dense[i])
    print(f"  Doc {i}: {vals}")

# %%
# Compare BoW vs TF-IDF side by side for one document
count_vec2 = CountVectorizer()
bow = count_vec2.fit_transform(documents).toarray()
tfidf_vec2 = TfidfVectorizer()
tfidf = tfidf_vec2.fit_transform(documents).toarray()

doc_idx = 0
feature_names = count_vec2.get_feature_names_out()

fig, axes = plt.subplots(1, 2, figsize=(14, 4))

# BoW
axes[0].barh(range(len(feature_names)), bow[doc_idx], color='steelblue')
axes[0].set_yticks(range(len(feature_names)))
axes[0].set_yticklabels(feature_names)
axes[0].set_title(f"BoW (Doc {doc_idx})")
axes[0].set_xlabel("Word Count")

# TF-IDF
axes[1].barh(range(len(feature_names)), tfidf[doc_idx], color='coral')
axes[1].set_yticks(range(len(feature_names)))
axes[1].set_yticklabels(feature_names)
axes[1].set_title(f"TF-IDF (Doc {doc_idx})")
axes[1].set_xlabel("TF-IDF Weight")

plt.suptitle(f"Bag of Words vs TF-IDF for: '{documents[doc_idx]}'", fontsize=12)
plt.tight_layout()
plt.show()

print("Notice: common words like 'the', 'was' get lower TF-IDF weights.")
print("Distinctive words like 'superb', 'great' get higher relative weights.")

# %% [markdown]
# ---
# ## 5. Text Classification: Sentiment Analysis
#
# Now let's put it all together and build a **text classifier**. We'll do
# **sentiment analysis** — predicting whether a movie review is positive or negative.
#
# The pipeline:
# 1. Create a dataset of labeled reviews
# 2. Preprocess the text
# 3. Convert to TF-IDF features
# 4. Train a classifier
# 5. Evaluate performance

# %%
# Step 1: Create a synthetic movie review dataset
# In real projects you'd load a dataset like IMDB reviews

reviews = [
    # Positive reviews (label = 1)
    "This movie was absolutely wonderful and I loved every minute of it",
    "Great acting and a beautiful storyline that kept me engaged throughout",
    "One of the best films I have seen this year truly amazing work",
    "The performances were outstanding and the direction was superb",
    "A heartwarming story with excellent characters and great dialogue",
    "Loved this film so much the cinematography was breathtaking",
    "Fantastic movie with a powerful message and brilliant performances",
    "An incredible film that I would recommend to everyone",
    "Beautiful storytelling and amazing visual effects throughout",
    "This is a masterpiece of cinema with perfect pacing and emotion",
    # Negative reviews (label = 0)
    "This movie was awful and a complete waste of my time",
    "Terrible acting and a boring plot that went absolutely nowhere",
    "One of the worst films I have ever seen completely unwatchable",
    "The script was horrible and the characters were so badly written",
    "A dull and lifeless movie with no redeeming qualities at all",
    "Hated this film the dialogue was cringeworthy and painful",
    "Awful movie with bad acting and a predictable boring storyline",
    "A disappointing film that fails on every level",
    "Poorly made with terrible visual effects and weak performances",
    "This is the worst movie of the year do not waste your money",
]

labels = [1]*10 + [0]*10  # 1 = positive, 0 = negative

print(f"Dataset: {len(reviews)} reviews")
print(f"  Positive: {sum(labels)}")
print(f"  Negative: {len(labels) - sum(labels)}")
print(f"\nExample positive: '{reviews[0]}'")
print(f"Example negative: '{reviews[10]}'")

# %%
# Step 2: Split into train/test sets
X_train, X_test, y_train, y_test = train_test_split(
    reviews, labels, test_size=0.3, random_state=42, stratify=labels
)

print(f"Training set: {len(X_train)} reviews")
print(f"Test set:     {len(X_test)} reviews")

# %%
# Step 3 & 4: Build a pipeline — TF-IDF + Logistic Regression
pipeline_lr = Pipeline([
    ('tfidf', TfidfVectorizer()),       # Convert text to TF-IDF features
    ('clf', LogisticRegression())        # Classify
])

# Train
pipeline_lr.fit(X_train, y_train)

# Predict on test set
y_pred_lr = pipeline_lr.predict(X_test)

print("Logistic Regression Results:")
print(f"Accuracy: {accuracy_score(y_test, y_pred_lr):.2f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred_lr, target_names=['Negative', 'Positive']))

# %%
# Let's also try Naive Bayes — a classic for text classification
pipeline_nb = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', MultinomialNB())
])

pipeline_nb.fit(X_train, y_train)
y_pred_nb = pipeline_nb.predict(X_test)

print("Naive Bayes Results:")
print(f"Accuracy: {accuracy_score(y_test, y_pred_nb):.2f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred_nb, target_names=['Negative', 'Positive']))

# %%
# Let's test on brand new reviews!
new_reviews = [
    "I absolutely loved this film it was wonderful",
    "Terrible movie do not watch it",
    "The acting was great and the story was moving",
    "Worst movie ever made a total disaster",
]

predictions = pipeline_lr.predict(new_reviews)

print("Predictions on new reviews:")
for review, pred in zip(new_reviews, predictions):
    sentiment = "Positive" if pred == 1 else "Negative"
    print(f"  [{sentiment:8s}] '{review}'")

# %%
# What words does the model find most informative?
feature_names = pipeline_lr.named_steps['tfidf'].get_feature_names_out()
coefficients = pipeline_lr.named_steps['clf'].coef_[0]

# Top positive and negative words
top_positive_idx = np.argsort(coefficients)[-10:]
top_negative_idx = np.argsort(coefficients)[:10]

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Most positive words
axes[0].barh(range(10), coefficients[top_positive_idx], color='green', alpha=0.7)
axes[0].set_yticks(range(10))
axes[0].set_yticklabels(feature_names[top_positive_idx])
axes[0].set_title("Top 10 Positive Words")
axes[0].set_xlabel("Coefficient Weight")

# Most negative words
axes[1].barh(range(10), coefficients[top_negative_idx], color='red', alpha=0.7)
axes[1].set_yticks(range(10))
axes[1].set_yticklabels(feature_names[top_negative_idx])
axes[1].set_title("Top 10 Negative Words")
axes[1].set_xlabel("Coefficient Weight")

plt.suptitle("Most Informative Words for Sentiment Classification", fontsize=12)
plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# ## 6. Word Embeddings (Introduction)
#
# ### The Limitation of BoW and TF-IDF
#
# BoW and TF-IDF treat each word as an independent feature. They have no concept
# of **word similarity**:
# - "great" and "wonderful" are as different as "great" and "terrible"
# - The vectors are **sparse** (mostly zeros) and **high-dimensional**
#
# ### Word Embeddings: Words as Dense Vectors
#
# Word embeddings represent each word as a **dense vector** (typically 50-300 dimensions)
# where **similar words have similar vectors**.
#
# The key insight: *words that appear in similar contexts have similar meanings*.
# - "The cat sat on the mat" and "The dog sat on the rug"
# - "cat" and "dog" appear in similar contexts -> similar vectors
#
# Famous algorithms:
# - **Word2Vec** (Google, 2013) — learns embeddings by predicting words from context
# - **GloVe** (Stanford, 2014) — learns from word co-occurrence statistics
# - **FastText** (Facebook, 2016) — handles subwords, works for rare words

# %%
# Let's simulate word embeddings to understand the concept
# In reality, these come from training on billions of words

# Pretend embeddings (3D for visualization)
# Similar words should have similar vectors
word_vectors = {
    # Positive sentiment words (cluster together)
    'great':     np.array([0.8, 0.9, 0.1]),
    'wonderful': np.array([0.85, 0.85, 0.15]),
    'excellent': np.array([0.9, 0.8, 0.1]),
    'amazing':   np.array([0.75, 0.95, 0.2]),
    # Negative sentiment words (cluster together)
    'terrible':  np.array([0.1, 0.15, 0.9]),
    'awful':     np.array([0.15, 0.1, 0.85]),
    'horrible':  np.array([0.1, 0.2, 0.95]),
    'bad':       np.array([0.2, 0.15, 0.8]),
    # Neutral words (somewhere in between)
    'movie':     np.array([0.5, 0.5, 0.5]),
    'film':      np.array([0.55, 0.48, 0.52]),
}

print("Word vectors (3D):")
for word, vec in word_vectors.items():
    print(f"  {word:12s} -> {vec}")


# %%
# Measure similarity using cosine similarity
def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Compare some word pairs
pairs = [
    ('great', 'wonderful'),    # should be similar
    ('terrible', 'awful'),     # should be similar
    ('great', 'terrible'),     # should be different
    ('movie', 'film'),         # should be similar
    ('movie', 'great'),        # somewhat different
]

print("Cosine Similarity between word pairs:")
print("-" * 50)
for w1, w2 in pairs:
    sim = cosine_similarity(word_vectors[w1], word_vectors[w2])
    bar = '#' * int(sim * 20)
    print(f"  {w1:12s} <-> {w2:12s}  sim = {sim:.3f}  {bar}")

# %%
# Visualize word embeddings in 2D
from sklearn.decomposition import PCA

words = list(word_vectors.keys())
vectors = np.array(list(word_vectors.values()))

# Reduce to 2D with PCA
pca = PCA(n_components=2)
vectors_2d = pca.fit_transform(vectors)

# Color by sentiment
colors = ['green']*4 + ['red']*4 + ['gray']*2

plt.figure(figsize=(8, 6))
plt.scatter(vectors_2d[:, 0], vectors_2d[:, 1], c=colors, s=100, zorder=5)

for i, word in enumerate(words):
    plt.annotate(word, (vectors_2d[i, 0], vectors_2d[i, 1]),
                 fontsize=12, ha='center', va='bottom',
                 xytext=(0, 8), textcoords='offset points')

plt.title("Word Embeddings Visualized in 2D\n(green=positive, red=negative, gray=neutral)")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print("Notice how similar words cluster together!")
print("This is the power of word embeddings — they capture meaning.")

# %% [markdown]
# ---
# ## 7. Transformers & LLMs (Brief Overview)
#
# ### The Evolution of NLP
#
# NLP has gone through several eras:
#
# | Era | Method | Key Idea |
# |-----|--------|----------|
# | 1990s-2000s | BoW / TF-IDF | Count words, ignore order |
# | 2013-2017 | Word2Vec / GloVe | Words as dense vectors |
# | 2017-present | **Transformers** | Attention mechanism, context-aware |
#
# ### The Attention Mechanism
#
# The **Transformer** architecture (introduced in the 2017 paper *"Attention Is All
# You Need"*) revolutionized NLP. The key innovation is the **attention mechanism**:
#
# - Previous models read text **left-to-right** (or right-to-left)
# - Attention lets the model look at **all words simultaneously** and decide
#   which words are most relevant to each other
#
# Example: In "The animal didn't cross the street because **it** was too tired"
# - What does "it" refer to? The **animal** (not the street)
# - Attention learns to connect "it" to "animal" across the sentence
#
# ### Key Models
#
# - **BERT** (Google, 2018) — reads text **bidirectionally**. Great for understanding
#   tasks (classification, Q&A, named entity recognition).
# - **GPT** (OpenAI, 2018-2024) — reads text **left-to-right**. Great for text
#   generation (chatbots, code, creative writing).
# - These are **pretrained** on massive text corpora (billions of words) and can be
#   **fine-tuned** for specific tasks with much less data.

# %%
# Visualize the attention concept with a simple heatmap
# This is a simplified illustration of how attention works

sentence = ["The", "movie", "was", "really", "great"]

# Simulated attention weights: how much each word attends to each other word
# when processing the word "great"
attention_weights = np.array([
    [0.05, 0.10, 0.05, 0.10, 0.70],  # "The" attends mostly to "great"
    [0.05, 0.30, 0.10, 0.15, 0.40],  # "movie" attends to itself and "great"
    [0.05, 0.15, 0.20, 0.20, 0.40],  # "was" attends to "great" and "really"
    [0.02, 0.08, 0.10, 0.30, 0.50],  # "really" attends strongly to "great"
    [0.05, 0.35, 0.10, 0.25, 0.25],  # "great" attends to "movie" and "really"
])

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(attention_weights, cmap='YlOrRd', aspect='auto')
ax.set_xticks(range(len(sentence)))
ax.set_xticklabels(sentence, fontsize=12)
ax.set_yticks(range(len(sentence)))
ax.set_yticklabels(sentence, fontsize=12)
ax.set_xlabel("Attending TO", fontsize=12)
ax.set_ylabel("Attending FROM", fontsize=12)
ax.set_title("Simplified Attention Weights\n(which words relate to which?)", fontsize=13)

for i in range(len(sentence)):
    for j in range(len(sentence)):
        ax.text(j, i, f"{attention_weights[i, j]:.2f}",
                ha='center', va='center', fontsize=10)

plt.colorbar(im, label='Attention Weight')
plt.tight_layout()
plt.show()

# %% [markdown]
# ### Bonus: Using a Pretrained Transformer with Hugging Face
#
# The `transformers` library by Hugging Face makes it incredibly easy to use
# pretrained models. The code below shows a sentiment analysis pipeline
# powered by a transformer model.
#
# **Note:** This requires the `transformers` and `torch` (or `tensorflow`)
# libraries. If you don't have them installed, you can skip this cell.
#
# ```bash
# pip install transformers torch
# ```

# %%
# OPTIONAL / BONUS — Requires: pip install transformers torch
# Uncomment the code below to try it out

# from transformers import pipeline
#
# # Load a pretrained sentiment analysis model
# sentiment_pipeline = pipeline("sentiment-analysis")
#
# # Analyze some reviews
# test_texts = [
#     "This movie was absolutely fantastic!",
#     "Terrible film, worst I've ever seen.",
#     "It was okay, nothing special.",
#     "The acting was superb and the story was deeply moving.",
# ]
#
# print("Transformer-based Sentiment Analysis:")
# print("-" * 60)
# for text in test_texts:
#     result = sentiment_pipeline(text)[0]
#     label = result['label']
#     score = result['score']
#     print(f"  [{label:8s} {score:.3f}] '{text}'")

print("(Uncomment the code above if you have transformers + torch installed)")
print("Pretrained transformers are far more accurate than our simple TF-IDF model!")


# %% [markdown]
# ---
# ## 8. Exercises
#
# ### Exercise 9.1 — Build a Text Preprocessing Function
#
# Write a function `clean_text(text)` that:
# 1. Converts to lowercase
# 2. Removes all characters except letters and spaces
# 3. Tokenizes (splits into words)
# 4. Removes stop words (use the `STOP_WORDS` set defined earlier)
# 5. Returns the cleaned tokens as a **list**
#
# Test it on the sample sentences provided.

# %%
# TODO: Implement clean_text
def clean_text(text):
    """Preprocess text: lowercase, remove punctuation, tokenize, remove stop words.
    Returns a list of cleaned tokens.
    """
    pass  # Your code here


# Test it
test_sentences = [
    "The Quick Brown Fox Jumps Over The Lazy Dog!",
    "NLP is an exciting area of AI, and it's growing FAST.",
    "I can't believe how GREAT this movie was!!!",
]

for s in test_sentences:
    print(f"Input:  '{s}'")
    print(f"Output: {clean_text(s)}")
    print()


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def clean_text(text):
    """Preprocess text: lowercase, remove punctuation, tokenize, remove stop words.
    Returns a list of cleaned tokens.
    """
    # 1. Lowercase
    text = text.lower()
    # 2. Remove non-letter characters (keep spaces)
    text = re.sub(r'[^a-z\s]', '', text)
    # 3. Tokenize
    tokens = text.split()
    # 4. Remove stop words
    tokens = [w for w in tokens if w not in STOP_WORDS]
    return tokens


# Test it
test_sentences = [
    "The Quick Brown Fox Jumps Over The Lazy Dog!",
    "NLP is an exciting area of AI, and it's growing FAST.",
    "I can't believe how GREAT this movie was!!!",
]

for s in test_sentences:
    print(f"Input:  '{s}'")
    print(f"Output: {clean_text(s)}")
    print()

# %% [markdown]
# ### Exercise 9.2 — Train a Text Classifier with TF-IDF + Naive Bayes
#
# Using the product review dataset below:
# 1. Split into train/test (70/30, random_state=42)
# 2. Build a pipeline: `TfidfVectorizer` + `MultinomialNB`
# 3. Train and evaluate with accuracy and classification report
# 4. Predict the sentiment of the new reviews provided

# %%
# Product review dataset
product_reviews = [
    "This product is amazing and works perfectly",
    "Excellent quality and fast shipping I am very happy",
    "Love this item it exceeded all my expectations",
    "Best purchase I have made in a long time highly recommend",
    "Great value for the price works exactly as described",
    "Wonderful product my whole family enjoys using it",
    "Perfect gift idea everyone loved it so much",
    "This is garbage it broke after one day of use",
    "Terrible quality the product arrived damaged and unusable",
    "Worst purchase ever complete waste of money do not buy",
    "Cheap materials and poor construction fell apart immediately",
    "Horrible experience the item does not work as advertised",
    "Very disappointed with this product returning it immediately",
    "Do not waste your money on this awful product",
]
product_labels = [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]

new_product_reviews = [
    "This product works wonderfully I love it",
    "Terrible item it broke on the first day",
    "Great quality and excellent customer service",
]

# TODO: Split the data
# X_train, X_test, y_train, y_test = ...

# TODO: Build the pipeline (TfidfVectorizer + MultinomialNB)
# pipeline = ...

# TODO: Train the pipeline
# ...

# TODO: Evaluate on test set
# y_pred = ...
# print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
# print(classification_report(y_test, y_pred, target_names=['Negative', 'Positive']))

# TODO: Predict on new reviews
# new_preds = ...
# for review, pred in zip(new_product_reviews, new_preds):
#     sentiment = "Positive" if pred == 1 else "Negative"
#     print(f"  [{sentiment}] '{review}'")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
# Split the data
X_train, X_test, y_train, y_test = train_test_split(
    product_reviews, product_labels, test_size=0.3, random_state=42
)

# Build the pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', MultinomialNB())
])

# Train
pipeline.fit(X_train, y_train)

# Evaluate
y_pred = pipeline.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Negative', 'Positive']))

# Predict on new reviews
print("\nPredictions on new reviews:")
new_preds = pipeline.predict(new_product_reviews)
for review, pred in zip(new_product_reviews, new_preds):
    sentiment = "Positive" if pred == 1 else "Negative"
    print(f"  [{sentiment}] '{review}'")

# %% [markdown]
# ### Exercise 9.3 — Compare BoW vs TF-IDF Accuracy
#
# Using the original movie review dataset from Section 5:
# 1. Build two pipelines:
#    - Pipeline A: `CountVectorizer` (BoW) + `MultinomialNB`
#    - Pipeline B: `TfidfVectorizer` (TF-IDF) + `MultinomialNB`
# 2. Train both on the same train split
# 3. Evaluate both on the same test split
# 4. Compare their accuracies — which one performs better?

# %%
# Dataset from Section 5
reviews = [
    "This movie was absolutely wonderful and I loved every minute of it",
    "Great acting and a beautiful storyline that kept me engaged throughout",
    "One of the best films I have seen this year truly amazing work",
    "The performances were outstanding and the direction was superb",
    "A heartwarming story with excellent characters and great dialogue",
    "Loved this film so much the cinematography was breathtaking",
    "Fantastic movie with a powerful message and brilliant performances",
    "An incredible film that I would recommend to everyone",
    "Beautiful storytelling and amazing visual effects throughout",
    "This is a masterpiece of cinema with perfect pacing and emotion",
    "This movie was awful and a complete waste of my time",
    "Terrible acting and a boring plot that went absolutely nowhere",
    "One of the worst films I have ever seen completely unwatchable",
    "The script was horrible and the characters were so badly written",
    "A dull and lifeless movie with no redeeming qualities at all",
    "Hated this film the dialogue was cringeworthy and painful",
    "Awful movie with bad acting and a predictable boring storyline",
    "A disappointing film that fails on every level",
    "Poorly made with terrible visual effects and weak performances",
    "This is the worst movie of the year do not waste your money",
]
labels = [1]*10 + [0]*10

X_train, X_test, y_train, y_test = train_test_split(
    reviews, labels, test_size=0.3, random_state=42, stratify=labels
)

# TODO: Build Pipeline A (BoW + Naive Bayes)
# pipeline_bow = ...

# TODO: Build Pipeline B (TF-IDF + Naive Bayes)
# pipeline_tfidf = ...

# TODO: Train both pipelines
# ...

# TODO: Evaluate both and print accuracies
# acc_bow = ...
# acc_tfidf = ...
# print(f"BoW + NB accuracy:    {acc_bow:.2f}")
# print(f"TF-IDF + NB accuracy: {acc_tfidf:.2f}")
# print(f"\nBetter method: {'TF-IDF' if acc_tfidf >= acc_bow else 'BoW'}")

# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
# Pipeline A: BoW + Naive Bayes
pipeline_bow = Pipeline([
    ('vectorizer', CountVectorizer()),
    ('clf', MultinomialNB())
])

# Pipeline B: TF-IDF + Naive Bayes
pipeline_tfidf = Pipeline([
    ('vectorizer', TfidfVectorizer()),
    ('clf', MultinomialNB())
])

# Train both
pipeline_bow.fit(X_train, y_train)
pipeline_tfidf.fit(X_train, y_train)

# Evaluate both
acc_bow = accuracy_score(y_test, pipeline_bow.predict(X_test))
acc_tfidf = accuracy_score(y_test, pipeline_tfidf.predict(X_test))

print(f"BoW + NB accuracy:    {acc_bow:.2f}")
print(f"TF-IDF + NB accuracy: {acc_tfidf:.2f}")
print(f"\nBetter method: {'TF-IDF' if acc_tfidf >= acc_bow else 'BoW'}")

# Detailed reports
print("\n--- BoW Classification Report ---")
print(classification_report(y_test, pipeline_bow.predict(X_test),
                            target_names=['Negative', 'Positive']))
print("--- TF-IDF Classification Report ---")
print(classification_report(y_test, pipeline_tfidf.predict(X_test),
                            target_names=['Negative', 'Positive']))

# %% [markdown]
# ---
# ## Key Takeaways
#
# - **Text must be converted to numbers** before ML models can use it
# - **Preprocessing** (lowercasing, tokenization, stop word removal, stemming) cleans raw text
# - **Bag of Words** counts word occurrences — simple but treats all words equally
# - **TF-IDF** improves on BoW by down-weighting common words
# - **Text classification** (e.g., sentiment analysis) follows the same ML workflow:
#   preprocess -> features -> train -> evaluate
# - **Word embeddings** represent words as dense vectors where similar words are close together
# - **Transformers** (BERT, GPT) use attention mechanisms and are the current state of the art
#
# ### What's Next?
#
# In the capstone project, you'll bring together everything from this course —
# data exploration, preprocessing, model building, evaluation — into a complete
# end-to-end ML project.
#
# ---
# **Next:** [Capstone Project ->](../10_capstone_project/01_capstone.ipynb)
