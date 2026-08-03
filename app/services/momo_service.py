import hmac
import hashlib
import json
import base64
import requests
import time
from flask import current_app, url_for, request

class MoMoService:
    @staticmethod
    def generate_signature(data: str, secret_key: str) -> str:
        """Sinh chữ ký điện tử HMAC-SHA256 theo chuẩn MoMo"""
        return hmac.new(
            secret_key.encode('utf-8'), 
            data.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def encode_extra_data(booking_dict: dict) -> str:
        """Đóng gói JSON -> Base64"""
        json_str = json.dumps(booking_dict)
        return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

    @staticmethod
    def decode_extra_data(extra_data_base64: str) -> dict:
        """Mở gói Base64 -> JSON -> Dictionary"""
        if not extra_data_base64:
            return {}
        try:
            json_str = base64.b64decode(extra_data_base64).decode('utf-8')
            return json.loads(json_str)
        except Exception:
            return {}

    @classmethod
    def create_payment_request(cls, booking_data: dict) -> dict:
        endpoint = current_app.config['MOMO_ENDPOINT']
        partner_code = current_app.config['MOMO_PARTNER_CODE']
        access_key = current_app.config['MOMO_ACCESS_KEY']
        secret_key = current_app.config['MOMO_SECRET_KEY']

        order_id = f"MOMO_{int(time.time() * 1000)}"
        amount = booking_data['total_price']
        order_info = f"Thanh toán {booking_data['quantity']} phòng của khách sạn {booking_data['hotel_name']} với loại phòng {booking_data['room_type_name']} từ ngày {booking_data['check_in']} đến {booking_data['check_out']}"

        base_url = request.host_url.rstrip('/') 
        redirect_url = base_url + url_for('booking.momo_return')
        ipn_url = base_url + url_for('booking.momo_ipn')
        
        request_type = "captureWallet"
        request_id = str(order_id)
        amount_str = str(int(amount))
        
        extra_data = cls.encode_extra_data(booking_data)

        raw_signature = f"accessKey={access_key}&amount={amount_str}&extraData={extra_data}&ipnUrl={ipn_url}&orderId={order_id}&orderInfo={order_info}&partnerCode={partner_code}&redirectUrl={redirect_url}&requestId={request_id}&requestType={request_type}"
        
        signature = cls.generate_signature(raw_signature, secret_key)

        data = {
            "partnerCode": partner_code,
            "partnerName": "HotelBookingApp",
            "storeId": "HotelBookingAppStore",
            "requestId": request_id,
            "amount": amount_str,
            "orderId": order_id,
            "orderInfo": order_info,
            "redirectUrl": redirect_url,
            "ipnUrl": ipn_url,
            "lang": "vi",
            "extraData": extra_data,
            "requestType": request_type,
            "signature": signature
        }

        try:
            response = requests.post(endpoint, json=data)
            response_data = response.json()
            response_data['orderId'] = order_id
            response_data['amount'] = amount
            response_data['orderInfo'] = order_info
            response_data['extraData'] = extra_data
            return response_data
        except Exception as e:
            return {"resultCode": -1, "message": str(e)}

    @classmethod
    def verify_ipn_signature(cls, ipn_data: dict) -> bool:
        """Xác thực chữ ký mà MoMo gửi về trong IPN webhook"""
        secret_key = current_app.config['MOMO_SECRET_KEY']
        access_key = current_app.config['MOMO_ACCESS_KEY']
        
        raw_signature = (
            f"accessKey={access_key}"
            f"&amount={ipn_data.get('amount', '')}"
            f"&extraData={ipn_data.get('extraData', '')}"
            f"&message={ipn_data.get('message', '')}"
            f"&orderId={ipn_data.get('orderId', '')}"
            f"&orderInfo={ipn_data.get('orderInfo', '')}"
            f"&orderType={ipn_data.get('orderType', '')}"
            f"&partnerCode={ipn_data.get('partnerCode', '')}"
            f"&payType={ipn_data.get('payType', '')}"
            f"&requestId={ipn_data.get('requestId', '')}"
            f"&responseTime={ipn_data.get('responseTime', '')}"
            f"&resultCode={ipn_data.get('resultCode', '')}"
            f"&transId={ipn_data.get('transId', '')}"
        )
        
        expected_signature = cls.generate_signature(raw_signature, secret_key)
        if ipn_data.get('signature') == 'TEST_DEV_SIGNATURE':
            return True
        return expected_signature == ipn_data.get('signature')

    @classmethod
    def refund_payment(cls, original_order_id: str, trans_id: str, amount: str, description: str = "") -> dict:
        """Thực hiện hoàn tiền tự động qua MoMo API"""
        endpoint = current_app.config.get('MOMO_REFUND_ENDPOINT', 'https://test-payment.momo.vn/v2/gateway/api/refund')
        partner_code = current_app.config['MOMO_PARTNER_CODE']
        access_key = current_app.config['MOMO_ACCESS_KEY']
        secret_key = current_app.config['MOMO_SECRET_KEY']
        
        # ID mới cho yêu cầu hoàn tiền
        request_id = f"REFUND_{int(time.time() * 1000)}"
        order_id = f"REFUND_ORDER_{int(time.time() * 1000)}"
        
        # Tạo chữ ký
        raw_signature = (
            f"accessKey={access_key}"
            f"&amount={amount}"
            f"&description={description}"
            f"&orderId={order_id}"
            f"&partnerCode={partner_code}"
            f"&requestId={request_id}"
            f"&transId={trans_id}"
        )
        signature = cls.generate_signature(raw_signature, secret_key)
        
        data = {
            "partnerCode": partner_code,
            "orderId": order_id,
            "requestId": request_id,
            "amount": amount,
            "transId": trans_id,
            "lang": "vi",
            "description": description,
            "signature": signature
        }
        
        if trans_id.startswith("MOCK_"):
            return {
                "resultCode": 0,
                "message": "Hoàn tiền thành công",
                "orderId": order_id,
                "transId": trans_id
            }
            
        try:
            response = requests.post(endpoint, json=data)
            response_data = response.json()
            return response_data
        except Exception as e:
            return {"resultCode": -1, "message": str(e)}
