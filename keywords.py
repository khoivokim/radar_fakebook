"""
Từ khóa & pattern nhận diện khách hàng tiềm năng ngành Bảng Hiệu Quảng Cáo
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
import re

@dataclass
class KeywordEngine:
    """
    Hệ thống từ khóa được thiết kế theo nguyên tắc:
    - Nhận diện Ý ĐỊNH MUA (intent keywords)
    - Nhận diện BỐI CẢNH (context keywords)  
    - Nhận diện CẢM XÚC (sentiment keywords)
    """
    
    # === 1. TỪ KHÓA Ý ĐỊNH MUA (Intent - điểm cao nhất) ===
    BUY_INTENT: List[str] = None
    
    # === 2. TỪ KHÓA BỐI CẢNH (Context - điểm trung bình) ===
    CONTEXT: List[str] = None
    
    # === 3. TỪ KHÓA CẢM XÚC TÍCH CỰC/NEGATIVE (Sentiment) ===
    POSITIVE_SENTIMENT: List[str] = None
    NEGATIVE_SENTIMENT: List[str] = None  # Cơ hội: "bảng hiệu cũ", "không thấy"
    
    # === 4. TỪ KHÓA ĐỊA ĐIỂM (Location signals) ===
    LOCATION_PATTERNS: List[str] = None
    
    def __post_init__(self):
        self.BUY_INTENT = [
            # Trực tiếp muốn làm
            "cần làm bảng hiệu", "muốn làm bảng hiệu", "làm bảng hiệu ở đâu",
            "làm bảng hiệu giá rẻ", "làm bảng hiệu uy tín", "làm bảng hiệu đẹp",
            "cần làm biển quảng cáo", "làm biển quảng cáo", "làm bảng quảng cáo",
            "đặt làm bảng hiệu", "đặt biển quảng cáo", "thi công bảng hiệu",
            "thiết kế bảng hiệu", "thiết kế biển quảng cáo",
            
            # Mở cửa hàng mới
            "chuẩn bị khai trương", "sắp khai trương", "mới mở cửa hàng",
            "mở tiệm mới", "mở quán mới", "mở shop mới", "mở salon",
            "mở spa", "mở nhà hàng", "mở quán cafe", "mở tiệm tóc",
            "mở văn phòng", "mở công ty", "mở phòng khám", "mở hiệu thuốc",
            
            # Cần thay mới
            "thay bảng hiệu mới", "sửa bảng hiệu", "thay biển quảng cáo",
            "bảng hiệu cũ rồi", "biển quảng cáo hỏng", "cần thay biển",
            
            # Hỏi giá
            "bảng hiệu giá bao nhiêu", "làm biển giá sao", "báo giá bảng hiệu",
            "giá bảng hiệu alu", "giá bảng hiệu led", "giá biển hiflex",
        ]
        
        self.CONTEXT = [
            # Loại bảng hiệu
            "bảng hiệu alu", "bảng hiệu mica", "bảng hiệu led", "bảng hiệu neon",
            "bảng hiệu hộp đèn", "bảng hiệu chữ nổi", "bảng hiệu inox",
            "biển hiflex", "biển bạt", "biển quảng cáo đèn led",
            "chữ nổi mica", "chữ nổi inox", "chữ nổi led", "logo công ty",
            "bảng tên công ty", "biển chỉ dẫn", "biển phòng ban",
            
            # Vật liệu
            "alu", "mica", "inox", "hiflex", "bạt hiflex", "led neon",
            "decal", "pp", "formex", "foam",
            
            # Dịch vụ liên quan
            "thi công quảng cáo", "làm đẹp mặt tiền", "trang trí mặt tiền",
            "bảng giá", "standee", "backdrop", "poster", "banner",
        ]
        
        self.POSITIVE_SENTIMENT = [
            "đẹp", "chất lượng", "uy tín", "nhanh", "rẻ", "hợp lý",
            "hài lòng", "khuyến mãi", "ưu đãi", "giá tốt"
        ]
        
        self.NEGATIVE_SENTIMENT = [
            "hỏng", "cũ", "xấu", "mờ", "tối", "không thấy", "không rõ",
            "bong tróc", "xuống cấp", "cần sửa", "cần thay"
        ]
        
        self.LOCATION_PATTERNS = [
            r"ở\s+([\w\s]+)", r"tại\s+([\w\s]+)", r"quận\s+([\w\s]+)",
            r"huyện\s+([\w\s]+)", r"phường\s+([\w\s]+)"
        ]
    
    def calculate_intent_score(self, text: str) -> Tuple[int, Dict]:
        """
        Tính điểm ý định mua (0-100) và trả về chi tiết phân tích
        """
        text_lower = text.lower()
        score = 0
        details = {
            "buy_intent_matches": [],
            "context_matches": [],
            "positive_matches": [],
            "negative_matches": [],
            "location_hints": [],
            "total_score": 0
        }
        
        # 1. Điểm ý định mua (mỗi match +25 điểm, max 50)
        for keyword in self.BUY_INTENT:
            if keyword in text_lower:
                details["buy_intent_matches"].append(keyword)
                score += 25
                if score >= 50:
                    break
        
        # 2. Điểm bối cảnh (mỗi match +10 điểm, max 30)
        for keyword in self.CONTEXT:
            if keyword in text_lower:
                details["context_matches"].append(keyword)
                score += 10
                if score >= 80:  # Cap tại 80 trước sentiment
                    break
        
        # 3. Điểm cảm xúc tích cực (+5 mỗi match, max 15)
        for keyword in self.POSITIVE_SENTIMENT:
            if keyword in text_lower:
                details["positive_matches"].append(keyword)
                score += 5
                if len(details["positive_matches"]) >= 3:
                    break
        
        # 4. Điểm cảm xúc tiêu cực (cũng là cơ hội! +10 mỗi match)
        for keyword in self.NEGATIVE_SENTIMENT:
            if keyword in text_lower:
                details["negative_matches"].append(keyword)
                score += 10
                if len(details["negative_matches"]) >= 2:
                    break
        
        # 5. Tìm địa điểm
        for pattern in self.LOCATION_PATTERNS:
            matches = re.findall(pattern, text_lower)
            details["location_hints"].extend(matches)
        
        # Cap score tại 100
        score = min(score, 100)
        details["total_score"] = score
        
        return score, details


# Singleton
keyword_engine = KeywordEngine()