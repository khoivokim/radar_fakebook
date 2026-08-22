"""
Hệ thống thông báo - Tự động gửi Telegram khi có lead mới
"""

import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict
import os


class LeadNotifier:
    # ⭐ DÙNG TRỰC TIẾP TOKEN & CHAT_ID (không cần biến môi trường)
    TELEGRAM_BOT_TOKEN = "8231667796:AAGSlM6joDmPIHCqI4iFi6_XSNXehor7g10"
    TELEGRAM_CHAT_ID = "5435332140"
    
    def send_message(self, message):

        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": self.TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": True
        }

        requests.post(url, json=payload, timeout=15)

    def __init__(self):
        self.notification_history = []
        self.email_sender = os.getenv("NOTIFY_EMAIL", "")
        self.email_password = os.getenv("NOTIFY_EMAIL_PASSWORD", "")

        # File lưu lịch sử đã gửi (tránh spam trùng)
        self.sent_history_file = "data/sent_leads.json"
        self.sent_post_ids = self._load_sent_history()

    def _load_sent_history(self) -> set:
        """Load danh sách post_id đã gửi để tránh spam trùng"""
        if os.path.exists(self.sent_history_file):
            try:
                with open(self.sent_history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('sent_ids', []))
            except:
                pass
        return set()

    def _save_sent_history(self):
        """Lưu danh sách post_id đã gửi"""
        os.makedirs("data", exist_ok=True)
        with open(self.sent_history_file, 'w', encoding='utf-8') as f:
            json.dump({'sent_ids': list(self.sent_post_ids)}, f, ensure_ascii=False, indent=2)

    def _is_already_sent(self, post_id: str) -> bool:
        """Kiểm tra đã gửi thông báo cho post này chưa"""
        return post_id in self.sent_post_ids

    def _mark_as_sent(self, post_id: str):
        """Đánh dấu đã gửi"""
        self.sent_post_ids.add(post_id)
        self._save_sent_history()

    def notify_console(self, lead: Dict):
        """In ra console"""
        print("\n" + "🎯"*30)
        print(f"🔥 PHÁT HIỆN LEAD NÓNG!")
        print(f"   Tác giả: {lead.get('author_name', 'Unknown')}")
        print(f"   Điểm: {lead.get('total_score', 0)}/100")
        print(f"   Loại: {lead.get('lead_type', 'unknown').upper()}")
        print(f"   Ngành: {lead.get('business_type', 'N/A')}")
        print(f"   Địa điểm: {lead.get('location_hint', 'N/A')}")
        print(f"   Link: {lead.get('permalink', 'N/A')}")
        print(f"   Hành động: {lead.get('suggested_action', '')}")
        print(f"   Nội dung: {lead.get('content', '')[:200]}...")
        print("🎯"*30 + "\n")

    def notify_telegram(self, lead: Dict) -> bool:
        """
        ⭐ GỬI THÔNG BÁO TELEGRAM - Chỉ gửi 1 lần cho mỗi lead
        """
        post_id = lead.get('post_id', '')

        # Kiểm tra đã gửi chưa
        if self._is_already_sent(post_id):
            print(f"   ⏭️  Lead này đã gửi Telegram trước đó, bỏ qua")
            return False

        # Xác định icon theo loại lead
        lead_type = lead.get('lead_type', 'cold')
        if lead_type == 'hot':
            icon = "🔥"
            urgency = "🚨 KHẨN CẤP!"
        elif lead_type == 'warm':
            icon = "🌡"
            urgency = "⚡ TIỀM NĂNG"
        else:
            icon = "❄️"
            urgency = "👀 THEO DÕI"

        # Tạo nội dung tin nhắn đẹp
        message = (
            f"{icon} <b>{urgency}</b>\n"
            f"{'─'*28}\n\n"
            f"👤 <b>Khách:</b> {lead.get('author_name', 'Unknown')}\n"
            f"📊 <b>Điểm:</b> {lead.get('total_score', 0)}/100\n"
            f"🏷 <b>Loại:</b> {lead.get('lead_type', 'unknown').upper()}\n"
            f"🏢 <b>Ngành:</b> {lead.get('business_type', 'N/A')}\n"
            f"📍 <b>Địa điểm:</b> {lead.get('location_hint', 'Chưa rõ')}\n\n"
            f"📝 <b>Nội dung:</b>\n"
            f"<i>{lead.get('content', '')[:350]}...</i>\n\n"
            f"💡 <b>Hành động:</b> {lead.get('suggested_action', '')}\n\n"
            f"⏰ <i>Gửi lúc: {datetime.now().strftime('%H:%M %d/%m/%Y')}</i>"
        )

        # ⭐ GỬI TRỰC TIẾP QUA API
        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': self.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }

        try:
            print(f"   📱 Đang gửi Telegram...")
            response = requests.post(url, json=payload, timeout=15)
            result = response.json()

            if result.get('ok'):
                print(f"   ✅ Gửi Telegram THÀNH CÔNG!")
                self._mark_as_sent(post_id)
                return True
            else:
                print(f"   ❌ Telegram lỗi: {result.get('description', 'Unknown error')}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Lỗi kết nối Telegram: {e}")
            return False

    def test_telegram(self):
        """⭐ TEST GỬI TIN NHẮN - Dùng để kiểm tra"""
        print("📱 Đang test gửi Telegram...")

        message = (
            f"🧪 <b>TEST RADAR FACEBOOK</b>\n"
            f"{'─'*28}\n\n"
            f"✅ Bot đang hoạt động!\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n\n"
            f"💡 Từ giờ, mỗi khi phát hiện lead Git, "
            f"bạn sẽ nhận thông báo tại đây."
        )

        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': self.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }

        try:
            response = requests.post(url, json=payload, timeout=15)
            result = response.json()

            if result.get('ok'):
                print("   ✅ Test thành công! Kiểm tra Telegram của bạn.")
                return True
            else:
                print(f"   ❌ Lỗi: {result}")
                return False
        except Exception as e:
            print(f"   ❌ Lỗi: {e}")
            return False

    def send_telegram_summary(self, new_leads: List[Dict], scan_time: str):
        """Gửi tổng kết sau mỗi lần quét"""
        if not new_leads:
            message = (
                f"📊 <b>BÁO CÁO QUÉT - {scan_time}</b>\n"
                f"{'─'*28}\n\n"
                f"📭 Không có lead mới trong đợt này."
            )
        else:
            hot_count = sum(1 for l in new_leads if l.get('lead_type') == 'hot')
            warm_count = sum(1 for l in new_leads if l.get('lead_type') == 'warm')

            message = (
                f"📊 <b>BÁO CÁO QUÉT - {scan_time}</b>\n"
                f"{'─'*28}\n\n"
                f"📈 Tổng mới: <b>{len(new_leads)}</b> leads\n"
                f"🔥 Hot: <b>{hot_count}</b> | 🌡 Warm: <b>{warm_count}</b>\n\n"
            )

            if hot_count > 0:
                message += "🔥 <b>Hot leads:</b>\n"
                for i, lead in enumerate([l for l in new_leads if l.get('lead_type') == 'hot'][:3], 1):
                    message += f"   {i}. {lead.get('author_name', 'Unknown')} ({lead.get('total_score', 0)}đ)\n"

        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': self.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }

        try:
            requests.post(url, json=payload, timeout=10)
        except:
            pass

    def notify_email(self, leads: List[Dict], recipient: str = None):
        if not self.email_sender or not self.email_password:
            return
        # ... (giữ nguyên code email cũ)

    def save_to_json(self, leads: List[Dict], filename: str = None):
        if filename is None:
            filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        filepath = os.path.join("data", filename)
        os.makedirs("data", exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(leads, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu {len(leads)} leads vào {filepath}")
        return filepath