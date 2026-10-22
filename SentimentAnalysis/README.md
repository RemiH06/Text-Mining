# Sentiment Analysis using N-grams

Project No. 1 (NLP course): binary sentiment classification of IMDb movie
reviews with unigram, bigram and trigram count features and three sklearn
classifiers (Naive Bayes, Logistic Regression, Linear SVM). Assignment:
`Sentiment_Analysis_Ngram_Assignment_v1.pdf`.

## Project structure

```
SentimentAnalysis/
├── data.py              # Download IMDb, load splits, carve dev out of train
├── preprocessing.py     # Part 1: cleaning, tokenization, negation-aware stopwords
├── features.py          # Part 2: CountVectorizer per n-gram range
├── models.py            # Part 3: NB / LR / SVM pipelines
├── evaluation.py        # Part 4: metrics, confusion matrices, length/rating breakdowns
├── error_analysis.py    # Part 5: misclassified reviews tagged with linguistic cues
├── run_pipeline.py      # Runs Parts 1-5 end to end
├── Sentiment_Analysis.ipynb  # Same pipeline step by step, with charts and error analysis (Spanish)
├── requirements.txt
├── data/                # IMDb archive + preprocessed cache (git-ignored)
├── results/             # CSVs and figures/ written by run_pipeline.py
└── report/              # 2-3 page report (deliverable)
```

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; use .venv/bin/activate elsewhere
pip install -r requirements.txt
```

## Running

```bash
python data.py           # downloads ~84 MB from Stanford, prints split sizes
python run_pipeline.py   # trains, evaluates and writes everything to results/
```

If Stanford's server is down, `data.py` falls back to the Hugging Face copy
(`stanfordnlp/imdb`), which has the same reviews but no star ratings.

For the notebook, select `.venv` as the kernel (in VS Code) or register it:

```bash
python -m ipykernel install --user --name sentiment-ngrams
```

## Design decisions

- **Splits:** the official 25k/25k train/test split is kept. 20% of train
  (stratified, seed 42) becomes the dev set used for model selection; test
  is used once, after refitting the chosen configs on train+dev.
- **Negation survives preprocessing:** `n't` is expanded to `not` and
  negation words are excluded from the stopword list, otherwise bigrams such
  as `not good` could never form.
- **`min_df=2`:** n-grams seen in only one review are dropped, which shrinks
  the trigram vocabulary drastically with negligible accuracy cost.
- **Star rating kept:** IMDb file names include the 1-10 rating, used to
  measure accuracy by polarity strength (reviews rated 4 or 7 are the
  hardest).
