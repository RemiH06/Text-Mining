"""Recolección con la YouTube Data API, en dos pasos para poder vetar videos entre ambos.

    python -m stance.collect search    # escribe data/videos.csv; pongan keep=0 a los que no sirvan
    python -m stance.collect comments  # baja comentarios; si se acaba la cuota, retoma al reintentar

La llave se lee de la variable KEY del archivo .env. No se guardan nombres de autores: el modelo no
los necesita y así el dataset no identifica a nadie.
"""
import argparse
import os

import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import COMMENTS_CSV, DATA, MAX_PAGES_PER_VIDEO, MAX_VIDEOS_PER_QUERY, QUERIES, ROOT, VIDEOS_CSV


def client():
    load_dotenv(ROOT / ".env")
    key = os.environ.get("KEY")
    if not key:
        raise SystemExit("Falta KEY en el archivo .env.")
    return build("youtube", "v3", developerKey=key, cache_discovery=False)


def search_videos(yt) -> pd.DataFrame:
    rows = []
    for side, queries in QUERIES.items():
        for query in queries:
            response = yt.search().list(
                part="snippet", q=query, type="video", maxResults=MAX_VIDEOS_PER_QUERY,
                relevanceLanguage="es", regionCode="MX",
            ).execute()
            rows += [
                {
                    "video_id": item["id"]["videoId"],
                    "side": side,
                    "query": query,
                    "channel": item["snippet"]["channelTitle"],
                    "title": item["snippet"]["title"],
                    "keep": 1,
                }
                for item in response["items"]
            ]
    videos = pd.DataFrame(rows).drop_duplicates(["video_id", "side"])
    # Un video que aparece en ambos bandos no dice nada sobre la postura.
    return videos.drop_duplicates("video_id", keep=False)


def video_comments(yt, video_id: str, side: str) -> list[dict]:
    rows, token = [], None
    for _ in range(MAX_PAGES_PER_VIDEO):
        response = yt.commentThreads().list(
            part="snippet", videoId=video_id, maxResults=100, textFormat="plainText",
            order="relevance", pageToken=token,
        ).execute()
        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]
            rows.append(
                {
                    "comment_id": comment["id"],
                    "video_id": video_id,
                    "side": side,
                    "text": comment["snippet"]["textDisplay"],
                }
            )
        token = response.get("nextPageToken")
        if not token:
            break
    return rows


def download_comments(yt) -> pd.DataFrame:
    videos = pd.read_csv(VIDEOS_CSV)
    done = pd.read_csv(COMMENTS_CSV) if COMMENTS_CSV.exists() else pd.DataFrame()
    seen = set(done["video_id"]) if len(done) else set()
    rows = []
    try:
        for video in videos[(videos["keep"] == 1) & ~videos["video_id"].isin(seen)].itertuples():
            try:
                rows += video_comments(yt, video.video_id, video.side)
            except HttpError as error:
                if b"quotaExceeded" in error.content:
                    print("Cuota agotada: se guarda lo obtenido; reintenta mañana.")
                    break
                print(f"Se omite {video.video_id}: HTTP {error.status_code}")
    finally:
        comments = pd.concat([done, pd.DataFrame(rows)], ignore_index=True)
        comments.to_csv(COMMENTS_CSV, index=False)
    return comments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=["search", "comments"])
    step = parser.parse_args().step
    DATA.mkdir(exist_ok=True)
    yt = client()
    if step == "search":
        videos = search_videos(yt)
        videos.to_csv(VIDEOS_CSV, index=False)
        print(videos["side"].value_counts().to_string())
    else:
        comments = download_comments(yt)
        print(comments["side"].value_counts().to_string())


if __name__ == "__main__":
    main()
