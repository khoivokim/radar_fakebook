"""
Cấu hình hệ thống Radar Facebook cho ngành Bảng Hiệu Quảng Cáo
"""

import os
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Config:
    # === Facebook API (Graph API - chỉ dùng cho trang công khai) ===
    FB_ACCESS_TOKEN: str = os.getenv("FB_ACCESS_TOKEN", "")
    FB_API_VERSION: str = "v18.0"
    
    # === Tìm kiếm trong nhóm công khai (không cần token) ===
    # Danh sách ID nhóm Facebook công khai liên quan đến kinh doanh
    TARGET_GROUPS: List[str] = None
    
    # === Từ khóa tìm kiếm ===
    KEYWORDS_FILE: str = "keywords.py"
    
    # === Ngưỡng điểm để đánh dấu lead tiềm năng ===
    HOT_LEAD_THRESHOLD: int = 70  # 0-100
    WARM_LEAD_THRESHOLD: int = 40
    
    # === Thời gian quét ===
    SCAN_INTERVAL_MINUTES: int = 30
    
    # === Khu vực địa lý (tùy chọn - để lọc khách hàng gần) ===
    TARGET_LOCATIONS: List[str] = None  # VD: ["Hà Nội", "TP.HCM", "Đà Nẵng"]
    
    def __post_init__(self):
        self.TARGET_GROUPS = self.TARGET_GROUPS or []
        self.TARGET_LOCATIONS = self.TARGET_LOCATIONS or [
            "TP.HCM", "Sài Gòn", "Long An", "Bình Dương", "Biên Hòa"
        ]

# Singleton config
config = Config()