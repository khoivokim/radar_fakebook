"""
Dashboard đơn giản hiển thị leads
"""

import json
import os
from datetime import datetime
from typing import List, Dict


class LeadDashboard:
    """
    Dashboard console để xem và quản lý leads
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def display_summary(self, leads: List[Dict]):
        """Hiển thị tổng quan leads"""
        if not leads:
            print("📭 Chưa có leads nào.")
            return
        
        hot = sum(1 for l in leads if l.get('lead_type') == 'hot')
        warm = sum(1 for l in leads if l.get('lead_type') == 'warm')
        cold = sum(1 for l in leads if l.get('lead_type') == 'cold')
        
        print("\n" + "="*60)
        print("📊 TỔNG QUAN LEADS")
        print("="*60)
        print(f"   🔥 Hot Leads:   {hot}")
        print(f"   🌡 Warm Leads:   {warm}")
        print(f"   ❄️  Cold Leads:   {cold}")
        print(f"   📈 Tổng cộng:    {len(leads)}")
        print("="*60)
    
    def display_hot_leads(self, leads: List[Dict], limit: int = 10):
        """Hiển thị top leads nóng"""
        hot_leads = [l for l in leads if l.get('lead_type') == 'hot']
        hot_leads.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        print(f"\n🔥 TOP {limit} HOT LEADS:")
        print("-" * 60)
        
        for i, lead in enumerate(hot_leads[:limit], 1):
            print(f"\n  #{i} [Điểm: {lead.get('total_score', 0)}/100]")
            print(f"     👤 {lead.get('author_name', 'Unknown')}")
            print(f"     🏢 {lead.get('business_type', 'N/A')}")
            print(f"     📍 {lead.get('location_hint', 'N/A')}")
            print(f"     💡 {lead.get('suggested_action', '')}")
            print(f"     🔗 {lead.get('permalink', 'N/A')}")
            print(f"     📝 {lead.get('content', '')[:150]}...")
    
    def display_by_location(self, leads: List[Dict]):
        """Thống kê leads theo địa điểm"""
        from collections import Counter
        
        locations = []
        for lead in leads:
            loc = lead.get('location_hint', '')
            if loc:
                locations.append(loc)
        
        if not locations:
            print("\n📍 Chưa có thông tin địa điểm.")
            return
        
        print("\n📍 THỐNG KÊ THEO ĐỊA ĐIỂM:")
        for loc, count in Counter(locations).most_common(10):
            print(f"   {loc}: {count} leads")
    
    def display_by_business(self, leads: List[Dict]):
        """Thống kê leads theo ngành"""
        from collections import Counter
        
        businesses = []
        for lead in leads:
            biz = lead.get('business_type', '')
            if biz and biz != 'Chưa xác định':
                # Tách nếu có nhiều loại
                for b in biz.split(', '):
                    businesses.append(b)
        
        if not businesses:
            print("\n🏢 Chưa có thông tin ngành.")
            return
        
        print("\n🏢 THỐNG KÊ THEO NGÀNH:")
        for biz, count in Counter(businesses).most_common(10):
            print(f"   {biz}: {count} leads")
    
    def export_csv(self, leads: List[Dict], filename: str = None):
        """Xuất leads ra CSV để dùng trong Excel/Google Sheets"""
        import csv
        
        if filename is None:
            filename = f"leads_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        filepath = os.path.join(self.data_dir, filename)
        
        if not leads:
            print("⚠️  Không có dữ liệu để xuất")
            return
        
        fieldnames = ['post_id', 'author_name', 'total_score', 'lead_type',
                     'business_type', 'location_hint', 'permalink', 
                     'suggested_action', 'content', 'created_time']
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for lead in leads:
                row = {k: lead.get(k, '') for k in fieldnames}
                writer.writerow(row)
        
        print(f"📄 Đã xuất CSV: {filepath}")
        return filepath