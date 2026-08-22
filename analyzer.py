"""
Phân tích bài đăng và chấm điểm khách hàng tiềm năng
"""

import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from keywords import keyword_engine


@dataclass
class LeadScore:
    """Kết quả phân tích một lead"""
    post_id: str
    author_name: str
    author_id: str
    content: str
    permalink: str
    created_time: str
    
    # Scores
    intent_score: int = 0  # 0-100
    urgency_score: int = 0  # 0-100 (dựa trên từ ngữ gấp)
    relevance_score: int = 0  # 0-100 (liên quan ngành)
    engagement_score: int = 0  # 0-100 (tương tác bài viết)
    
    # Phân loại
    lead_type: str = "cold"  # cold | warm | hot
    
    # Chi tiết
    matched_keywords: Dict = None
    location_hint: str = ""
    business_type: str = ""  # Loại hình kinh doanh (nếu detect được)
    suggested_action: str = ""
    
    def __post_init__(self):
        if self.matched_keywords is None:
            self.matched_keywords = {}
    
    @property
    def total_score(self) -> int:
        """Tổng điểm tổng hợp"""
        # Trọng số: intent 40%, urgency 20%, relevance 30%, engagement 10%
        total = (
            self.intent_score * 0.4 +
            self.urgency_score * 0.2 +
            self.relevance_score * 0.3 +
            self.engagement_score * 0.1
        )
        return int(total)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['total_score'] = self.total_score
        return data


class LeadAnalyzer:
    """
    Engine phân tích và chấm điểm leads
    """
    
    # Từ khóa gấp/urgency
    URGENCY_KEYWORDS = [
        "gấp", "khẩn", "nhanh", "trong tuần", "trong ngày", "sớm nhất",
        "càng sớm càng tốt", "ai làm được", "cần ngay", "cần gấp",
        "khai trương tuần sau", "khai trương tháng này"
    ]
    
    # Pattern nhận diện loại hình kinh doanh
    BUSINESS_PATTERNS = {
        "nhà hàng": ["nhà hàng", "quán ăn", "nhà hàng mới", "mở nhà hàng"],
        "cafe": ["quán cafe", "tiệm cafe", "coffee shop", "mở quán cafe"],
        "salon/tóc": ["tiệm tóc", "salon tóc", "mở salon", "tiệm nail"],
        "spa/thẩm mỹ": ["spa", "thẩm mỹ viện", "tiệm massage", "mở spa"],
        "shop/thời trang": ["shop", "cửa hàng thời trang", "boutique", "mở shop"],
        "phòng khám": ["phòng khám", "phòng mạch", "mở phòng khám"],
        "nhà thuốc": ["nhà thuốc", "hiệu thuốc", "mở nhà thuốc"],
        "văn phòng": ["văn phòng", "công ty", "mở văn phòng", "mở công ty"],
        "trường học": ["trung tâm", "trường", "mở lớp", "mở trung tâm"],
    }
    
    def __init__(self):
        self.keyword_engine = keyword_engine
    
    def analyze_post(self, post: Dict) -> LeadScore:
        """
        Phân tích một bài đăng và trả về LeadScore
        """
        content = post.get('content', '')
        if not content:
            return None
        
        # 1. Tính điểm ý định mua
        intent_score, keyword_details = self.keyword_engine.calculate_intent_score(content)
        
        # 2. Tính điểm urgency
        urgency_score = self._calculate_urgency(content)
        
        # 3. Tính điểm relevance (dựa trên số từ khóa ngành match)
        relevance_score = min(len(keyword_details.get('context_matches', [])) * 15, 100)
        
        # 4. Tính điểm engagement
        engagement_score = self._calculate_engagement(post)
        
        # 5. Xác định loại hình kinh doanh
        business_type = self._detect_business_type(content)
        
        # 6. Xác định location
        location = self._extract_location(content, keyword_details)
        
        # 7. Phân loại lead
        total = int(
            intent_score * 0.4 +
            urgency_score * 0.2 +
            relevance_score * 0.3 +
            engagement_score * 0.1
        )
        
        if total >= 70:
            lead_type = "hot"
        elif total >= 40:
            lead_type = "warm"
        else:
            lead_type = "cold"
        
        # 8. Gợi ý hành động
        suggested_action = self._suggest_action(lead_type, business_type, urgency_score)
        
        return LeadScore(
            post_id=post.get('post_id', ''),
            author_name=post.get('author_name', 'Unknown'),
            author_id=post.get('author_id', ''),
            content=content[:500],  # Giới hạn độ dài
            permalink=post.get('permalink', ''),
            created_time=post.get('created_time', ''),
            intent_score=intent_score,
            urgency_score=urgency_score,
            relevance_score=relevance_score,
            engagement_score=engagement_score,
            lead_type=lead_type,
            matched_keywords=keyword_details,
            location_hint=location,
            business_type=business_type,
            suggested_action=suggested_action
        )
    
    def _calculate_urgency(self, text: str) -> int:
        """Tính điểm gấp/urgency (0-100)"""
        text_lower = text.lower()
        score = 0
        
        for keyword in self.URGENCY_KEYWORDS:
            if keyword in text_lower:
                score += 25
        
        return min(score, 100)
    
    def _calculate_engagement(self, post: Dict) -> int:
        """Tính điểm tương tác dựa trên likes, comments, shares"""
        likes = post.get('likes_count', 0)
        comments = post.get('comments_count', 0)
        shares = post.get('shares_count', 0)
        
        # Công thức đơn giản: likes*1 + comments*3 + shares*5
        engagement = likes * 1 + comments * 3 + shares * 5
        
        # Normalize về 0-100 (giả sử max engagement = 500)
        return min(int(engagement / 5), 100)
    
    def _detect_business_type(self, text: str) -> str:
        """Nhận diện loại hình kinh doanh từ nội dung"""
        text_lower = text.lower()
        
        detected = []
        for biz_type, patterns in self.BUSINESS_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    detected.append(biz_type)
                    break
        
        return ", ".join(detected) if detected else "Chưa xác định"
    
    def _extract_location(self, text: str, keyword_details: Dict) -> str:
        """Trích xuất địa điểm từ nội dung"""
        locations = keyword_details.get('location_hints', [])
        if locations:
            # Lọc location hợp lệ (loại bỏ stop words)
            valid_locations = [loc.strip() for loc in locations if len(loc.strip()) > 2]
            return ", ".join(valid_locations[:2])  # Lấy tối đa 2 location
        return ""
    
    def _suggest_action(self, lead_type: str, business_type: str, urgency: int) -> str:
        """Gợi ý hành động tiếp theo"""
        if lead_type == "hot":
            if urgency > 60:
                return "🔥 LIÊN HỆ NGAY LẬP TỨC - Lead nóng + gấp!"
            return "📞 Gọi điện/ngắn tin trong vòng 2 giờ - Lead rất tiềm năng"
        elif lead_type == "warm":
            return "💬 Comment tư vấn chuyên nghiệp + inbox báo giá"
        else:
            return "👀 Theo dõi, tương tác bài viết để build relationship"
    
    def analyze_batch(self, posts: List[Dict]) -> List[LeadScore]:
        """Phân tích hàng loạt bài đăng"""
        results = []
        for post in posts:
            try:
                score = self.analyze_post(post)
                if score and score.total_score > 20:  # Chỉ giữ leads có điểm > 20
                    results.append(score)
            except Exception as e:
                print(f"❌ Lỗi phân tích post {post.get('post_id')}: {e}")
        
        # Sắp xếp theo total_score giảm dần
        results.sort(key=lambda x: x.total_score, reverse=True)
        return results
    
    def export_hot_leads(self, leads: List[LeadScore], threshold: int = 70) -> List[Dict]:
        """Lọc và xuất leads nóng"""
        hot_leads = [lead for lead in leads if lead.total_score >= threshold]
        return [lead.to_dict() for lead in hot_leads]