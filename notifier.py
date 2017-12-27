import json
import twilio
from twilio.rest import Client

with open("config.json") as f:
    config = json.load(f)
    TWILIO_SID = config["TWILIO_SID"]
    TWILIO_TOKEN = config["TWILIO_TOKEN"]
    TWILIO_FROM = config["TWILIO_FROM"]
    TWILIO_TO = config["TWILIO_TO"]


class Notifier:
    def __init__(self):
        self.client = Client(TWILIO_SID, TWILIO_TOKEN)

    def send(self, msg):
        try:
            ids = []
            for receiver in TWILIO_TO:
                message = self.client.messages.create(
                    to=receiver,
                    from_=TWILIO_FROM,
                    body="Mcafee Bot: " + msg)
                ids.append(message.sid)
            return ids
        except twilio.TwilioRestException as e:
            print(e)

    def buy(self, coin):
        self.send("Consider buying " + str(coin))


if __name__ == "__main__":
    nofifier = Notifier()
