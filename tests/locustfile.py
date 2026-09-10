from datetime import date, timedelta
import random

from locust import HttpUser, task, between


class HotelBookingUser(HttpUser):
    # Mỗi user nghỉ 1-3 giây giữa các thao tác
    wait_time = between(1, 3)

    # Dựa trên DB bạn vừa test Postman:
    # hotel 1 có room_type 1, 2, 3
    hotel_id = 1
    room_type_ids = [1, 2, 3]

    def random_dates(self):
        """
        Sinh khoảng ngày hợp lệ trong tương lai.
        """
        check_in = date.today() + timedelta(
            days=random.randint(1, 20)
        )

        check_out = check_in + timedelta(
            days=random.randint(1, 4)
        )

        return check_in.isoformat(), check_out.isoformat()

    @task(3)
    def check_availability(self):
        check_in, check_out = self.random_dates()

        with self.client.get(
            f"/api/hotel/{self.hotel_id}/availability",
            params={
                "check_in": check_in,
                "check_out": check_out,
            },
            name="/api/hotel/[hotel_id]/availability",
            catch_response=True,
        ) as response:

            if response.status_code != 200:
                response.failure(
                    f"HTTP {response.status_code}"
                )
                return

            try:
                data = response.json()
            except Exception:
                response.failure("Response không phải JSON")
                return

            if not isinstance(data, dict):
                response.failure("Response không phải JSON object")
                return

            response.success()

    @task(2)
    def calculate_price(self):
        check_in, check_out = self.random_dates()

        payload = {
            "check_in": check_in,
            "check_out": check_out,
            "quantity": random.randint(1, 3),
            "room_type_id": random.choice(self.room_type_ids),
        }

        with self.client.post(
            "/api/booking/calculate-price",
            json=payload,
            name="/api/booking/calculate-price",
            catch_response=True,
        ) as response:

            if response.status_code != 200:
                response.failure(
                    f"HTTP {response.status_code}: "
                    f"{response.text[:100]}"
                )
                return

            try:
                data = response.json()
            except Exception:
                response.failure("Response không phải JSON")
                return

            required_fields = [
                "total_price",
                "average_daily_price",
                "base_price",
                "quantity",
                "days",
            ]

            for field in required_fields:
                if field not in data:
                    response.failure(
                        f"Thiếu field {field}"
                    )
                    return

            if data["days"] <= 0:
                response.failure(
                    f"days không hợp lệ: {data['days']}"
                )
                return

            if data["total_price"] < 0:
                response.failure(
                    f"total_price âm: {data['total_price']}"
                )
                return

            response.success()