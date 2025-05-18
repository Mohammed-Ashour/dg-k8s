
class Alerting:
    @staticmethod
    def send_alert(msg: str, level: str, client_id: str = None):
        # Logic to send the alert
        print(f"[{level}] [client_id:{client_id}] alert: {msg}")

