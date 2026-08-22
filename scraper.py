"""
Scraper thu thập dữ liệu công khai từ Facebook - Chỉ lấy TIN MỚI
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from urllib.parse import quote


@dataclass
class FacebookPost:
    post_id: str
    author_name: str
    author_id: str
    content: str
    created_time: str
    permalink: str
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    is_public: bool = True
    group_name: Optional[str] = None
    location_hint: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class FacebookRadarScraper:
    def __init__(self, access_token: str = None, api_version: str = "v18.0"):
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{api_version}"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        })
        self.last_request_time = 0
        self.min_delay = 1.5

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()

    def _get_since_time(self, hours_back: int = 24) -> str:
        """
        Tính thời điểm 'từ khi nào' để chỉ lấy tin mới
        Mặc định: 24 giờ trước
        """
        since = datetime.utcnow() - timedelta(hours=hours_back)
        return since.strftime('%Y-%m-%dT%H:%M:%S')

    def search_public_pages(self, keyword: str, limit: int = 25, hours_back: int = 24) -> List[Dict]:
        """
        Tìm kiếm bài đăng công khai CHỈ TRONG KHOẢNG THỜI GIAN GẦN ĐÂY
        """
        if not self.access_token:
            print("⚠️  Cần FB_ACCESS_TOKEN để tìm kiếm qua API")
            return []

        self._rate_limit()

        since_time = self._get_since_time(hours_back)

        url = f"{self.base_url}/search"
        params = {
            'q': keyword,
            'type': 'post',
            'fields': 'id,message,created_time,from,permalink_url,likes.summary(true),comments.summary(true),shares',
            'limit': limit,
            'since': since_time,  # ⭐ CHỈ LẤY TIN TỪ since_time TRỞ ĐI
            'access_token': self.access_token
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            posts = []
            for item in data.get('data', []):
                # Kiểm tra thời gian thực sự để đảm bảo chỉ lấy tin mới
                created_time = item.get('created_time', '')
                post_datetime = datetime.strptime(created_time, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)

                # Bỏ qua nếu bài quá cũ
                if post_datetime < datetime.utcnow() - timedelta(hours=hours_back):
                    continue

                post = FacebookPost(
                    post_id=item.get('id', ''),
                    author_name=item.get('from', {}).get('name', 'Unknown'),
                    author_id=item.get('from', {}).get('id', ''),
                    content=item.get('message', ''),
                    created_time=created_time,
                    permalink=item.get('permalink_url', ''),
                    likes_count=item.get('likes', {}).get('summary', {}).get('total_count', 0),
                    comments_count=item.get('comments', {}).get('summary', {}).get('total_count', 0),
                    shares_count=item.get('shares', {}).get('count', 0) if item.get('shares') else 0
                )
                posts.append(post.to_dict())

            if posts:
                print(f"   📄 Tìm thấy {len(posts)} bài đăng MỚI (trong {hours_back}h qua)")
            else:
                print(f"   📭 Không có tin mới (trong {hours_back}h qua)")

            return posts

        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi API: {e}")
            return []

    def search_with_time_filter(self, keyword: str, hours_back: int = 2, limit: int = 25) -> List[Dict]:
        """
        ⭐ HÀM MỚI: Quét tin cực mới (mặc định 2 giờ) - dùng cho monitor liên tục
        """
        return self.search_public_pages(keyword, limit=limit, hours_back=hours_back)    

    def simulate_manual_research(self, keywords):

        results = []

        print("\n" + "=" * 60)
        print("📋 HƯỚNG DẪN TÌM TIN MỚI TRÊN FACEBOOK")
        print("=" * 60)

        print("DEBUG keywords =", keywords)
        print("DEBUG type =", type(keywords))

        for keyword in keywords:

            print("DEBUG keyword =", repr(keyword))

            url = f"https://www.facebook.com/search/posts/?q={quote(keyword)}"

            print(f"\n🔎 Từ khóa: '{keyword}'")
            print(f"👉 {url}")

            results.append({
                "keyword": keyword,
                "facebook_search_url": url,
                "posts_found": []
            })

        return results

    def fetch_page_posts(self, page_id: str, since: str = None, limit: int = 25, hours_back: int = 24) -> List[Dict]:
        if not self.access_token:
            return []

        self._rate_limit()

        url = f"{self.base_url}/{page_id}/posts"
        params = {
            'fields': 'id,message,created_time,permalink_url,likes.summary(true),comments.summary(true)',
            'limit': limit,
            'access_token': self.access_token
        }

        if since:
            params['since'] = since
        else:
            params['since'] = self._get_since_time(hours_back)

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            posts = []
            for item in data.get('data', []):
                created_time = item.get('created_time', '')
                post_datetime = datetime.strptime(created_time, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)

                if post_datetime < datetime.utcnow() - timedelta(hours=hours_back):
                    continue

                post = FacebookPost(
                    post_id=item.get('id', ''),
                    author_name="Page Post",
                    author_id=page_id,
                    content=item.get('message', ''),
                    created_time=created_time,
                    permalink=item.get('permalink_url', ''),
                    likes_count=item.get('likes', {}).get('summary', {}).get('total_count', 0),
                    comments_count=item.get('comments', {}).get('summary', {}).get('total_count', 0)
                )
                posts.append(post.to_dict())

            return posts

        except Exception as e:
            print(f"❌ Lỗi lấy posts từ page {page_id}: {e}")
            return []