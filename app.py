import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import numpy as np

st.set_page_config(page_title="📊 유튜브 채널 분석기", page_icon="📺", layout="centered")
st.title("📊 유튜브 채널 분석기")
st.write("채널 ID를 입력하면 기본 통계와 인기 영상을 분석해드립니다!")

api_key = st.text_input("유튜브 API Key 입력")
channel_id = st.text_input("분석할 채널 ID 입력")

if st.button("분석 시작") and api_key and channel_id:
    youtube = build("youtube", "v3", developerKey=api_key)
    
    # 채널 정보 가져오기
    channel_response = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id
    ).execute()
    
    if channel_response["items"]:
        channel = channel_response["items"][0]
        snippet = channel['snippet']
        stats = channel['statistics']
        st.subheader(f"채널명: {snippet['title']}")
        st.write(f"구독자 수: {stats.get('subscriberCount','비공개')}")
        st.write(f"총 동영상 수: {stats.get('videoCount','0')}")
        st.write(f"총 조회수: {stats.get('viewCount','0')}")
        
        uploads_playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        videos = []
        nextPageToken = None
        
        while True:
            pl_request = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist,
                maxResults=50,
                pageToken=nextPageToken
            ).execute()
            
            for item in pl_request["items"]:
                vid = item["snippet"]
                videos.append({
                    "title": vid["title"],
                    "publishedAt": vid["publishedAt"],
                    "videoId": vid["resourceId"]["videoId"]
                })
            nextPageToken = pl_request.get("nextPageToken")
            if not nextPageToken:
                break
        
        # 최근 5개 영상
        st.write("### 최근 업로드 동영상 (Top5)")
        for v in videos[-5:]:
            st.write(f"- {v['title']} ({v['publishedAt'][:10]})")
        
        # 인기 영상 Top3 (조회수 기준)
        video_stats = []
        for v in videos:
            vid_stats = youtube.videos().list(
                part="statistics",
                id=v["videoId"]
            ).execute()
            if vid_stats["items"]:
                vs = vid_stats["items"][0]["statistics"]
                video_stats.append({
                    "title": v["title"],
                    "views": int(vs.get("viewCount",0)),
                    "likes": int(vs.get("likeCount",0))
                })
        
        df = pd.DataFrame(video_stats)
        if not df.empty:
            st.write("### 인기 영상 Top3")
            top3 = df.sort_values("views", ascending=False).head(3)
            for idx, row in top3.iterrows():
                st.write(f"- {row['title']} | 조회수: {row['views']} | 좋아요: {row['likes']}")
            
            st.write("### 평균 통계")
            st.write(f"평균 조회수: {int(df['views'].mean())}")
            st.write(f"평균 좋아요 수: {int(df['likes'].mean())}")
    else:
        st.error("채널 정보를 가져올 수 없습니다. 채널 ID를 확인하세요.")
