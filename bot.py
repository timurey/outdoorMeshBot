import meshtastic
import meshtastic.serial_interface
from meshtastic import tcp_interface
from pubsub import pub
import time
import argparse
from weather import WeatherForecast

class MeshtasticBot:
    def __init__(self, connection_type='serial', hostname=None, serial_port=None):
        self.interface = None
        self.setup_connection(connection_type, hostname, serial_port)
        self.setup_subscribers()

    def setup_connection(self, connection_type, hostname, serial_port):
        if connection_type == 'wifi':
            self.interface = tcp_interface.TCPInterface(hostname=hostname)
        else:
            self.interface = meshtastic.serial_interface.SerialInterface(devPath=serial_port)

    def setup_subscribers(self):
        pub.subscribe(self.on_receive, "meshtastic.receive")
        pub.subscribe(self.on_connection, "meshtastic.connection.established")

    def on_receive(self, packet, interface):
        from_id = packet.get('fromId')
        if packet.get('decoded', {}).get('portnum') == 'TEXT_MESSAGE_APP':
            message = packet.get('decoded', {}).get('text', '').strip()
            print(f"Received message from {from_id}: {message}")
            if message.startswith('#'):
                if message.startswith('#weather') or message.startswith('#天氣') or message.startswith('#天气'):
                    self.handle_weather_command(from_id, message)
                elif message in ('#test', '#測試', '#测试'):
                    self.send_private_message(from_id, f"Test message from your nodeID {from_id}")
                else:
                    self.send_private_message(from_id, "Unknown command")

    def on_connection(self, interface, topic=pub.AUTO_TOPIC):
        print("Connected to Meshtastic device")

    def send_private_message(self, to_id, message):
        self.interface.sendText(message, destinationId=to_id)
        print(f"Sent message to {to_id}: {message[:50]}")

    def handle_weather_command(self, to_id, message):
        parts = message.split()
        
        if len(parts) == 1:
            node_info = self.interface.nodes.get(to_id)
            if node_info and 'position' in node_info:
                position = node_info['position']
                if 'latitude' in position and 'longitude' in position:
                    latitude = position['latitude']
                    longitude = position['longitude']
                else:
                    self.send_private_message(to_id, "Could not find your location. Please provide coordinates: #weather <latitude> <longitude> [hours]")
                    return
            else:
                self.send_private_message(to_id, "Could not find your location. Please provide coordinates: #weather <latitude> <longitude> [hours]")
                return
        elif len(parts) in [3, 4]:
            latitude, longitude = float(parts[1]), float(parts[2])
        else:
            self.send_private_message(to_id, "Usage: #weather <latitude> <longitude> [hours]")
            return

        forecast_hours = int(parts[3]) if len(parts) == 4 else 3

        weather_forecast = WeatherForecast(latitude=latitude, longitude=longitude)
        weather_forecast.fetch_forecast(forecast_hours)
        forecasts = weather_forecast.get_forecast(forecast_hours)

        if not forecasts:
            self.send_private_message(to_id, "No forecast data available.")
            return

        summary_message = f"Weather Forecast for {latitude}, {longitude} ({forecast_hours} hours)"
        time.sleep(5)
        self.send_private_message(to_id, summary_message)
        time.sleep(5)

        for forecast in forecasts:
            forecast_message = f"🕒 {forecast['time']} | 🌡 {forecast['temperature_2m']}°C | 🌧 {forecast['precipitation']}mm"
            self.send_private_message(to_id, forecast_message)
            time.sleep(10)

    def run(self):
        print("Bot is running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description='Meshtastic Bot with Weather Functionality')
    parser.add_argument('--connection-type', choices=['serial', 'wifi'], default='serial')
    parser.add_argument('--hostname')
    parser.add_argument('--serial-port')

    args = parser.parse_args()

    bot = MeshtasticBot(connection_type=args.connection_type, hostname=args.hostname, serial_port=args.serial_port)
    bot.run()

if __name__ == "__main__":
    main()
