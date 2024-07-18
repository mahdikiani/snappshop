import base64
import datetime
import json


class JWT(str):
    def decode(self) -> dict:
        def base64_url_decode(input):
            # Add padding if necessary
            input += "=" * (4 - (len(input) % 4))
            return base64.urlsafe_b64decode(input)

        try:
            jwt_token = self
            _, payload, _ = jwt_token.split(".")

            # Decode the payload
            decoded_payload = base64_url_decode(payload)
            payload_data = json.loads(decoded_payload)

            return payload_data
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def expired(self) -> bool:
        payload = self.decode()
        if not payload:
            return True

        exp = payload.get("exp", None)
        if not exp:
            return True

        exp_date = datetime.datetime.fromtimestamp(exp, datetime.UTC)
        now = datetime.datetime.now(datetime.UTC)

        return now > exp_date
