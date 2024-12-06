import meshtastic
import meshtastic.serial_interface
import meshtastic.tcp_interface
from pubsub import pub
import time
import argparse
import re  # For optional enhanced command parsing
import logging  # For logging

# Import WeatherFetcher
from weather_request import WeatherFetcher

# Import the TEXT_MESSAGE_APP constant
from meshtastic import portnums

class MeshtasticBot:
    def __init__(self, connection_type='serial', hostname=None, serial_port=None):
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,  # Capture all levels of logs
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

        self.interface = None
        self.setup_connection(connection_type, hostname, serial_port)
        self.setup_subscribers()

    def setup_connection(self, connection_type, hostname, serial_port):
        try:
            if connection_type == 'wifi':
                if not hostname:
                    raise ValueError("Hostname is required for WiFi connection")
                self.interface = meshtastic.tcp_interface.TCPInterface(hostname=hostname)
                self.logger.info(f"Connected via WiFi to {hostname}")
            else:  # serial
                if not serial_port:
                    raise ValueError("Serial port path is required for serial connection")
                self.interface = meshtastic.serial_interface.SerialInterface(devPath=serial_port)
                self.logger.info(f"Connected via Serial on {serial_port}")
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            raise

    def setup_subscribers(self):
        pub.subscribe(self.on_receive, "meshtastic.receive")
        pub.subscribe(self.on_connection, "meshtastic.connection.established")
        self.logger.debug("Subscribers for 'meshtastic.receive' and 'meshtastic.connection.established' set up")

    def on_receive(self, packet, interface):
        try:
            self.logger.debug(f"Received packet: {packet}")
            # Check if it's a text message
            portnum = packet.get('decoded', {}).get('portnum')
            self.logger.debug(f"Port number: {portnum}")

            if portnum == portnums.PORT_TEXT_MESSAGE:
                message = packet.get('decoded', {}).get('text', '').strip()
                from_id = packet.get('fromId')
                self.logger.info(f"Received message from {from_id}: {message}")

                # Define command patterns (optional)
                test_pattern = re.compile(r'^#test$', re.IGNORECASE)
                weather_pattern = re.compile(r'^#weather\s+(.+)$', re.IGNORECASE)

                # Check for #test command
                if test_pattern.match(message):
                    self.logger.info("Detected #test command")
                    self.send_private_message(from_id, "receive a test message")
                else:
                    weather_match = weather_pattern.match(message)
                    if weather_match:
                        location = weather_match.group(1).strip()
                        self.logger.info(f"Detected #weather command with location: {location}")
                        weather_fetcher = WeatherFetcher(location)
                        weather_data = weather_fetcher.get_weather()
                        self.send_private_message(from_id, weather_data)
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def on_connection(self, interface, topic=pub.AUTO_TOPIC):
        self.logger.info("Connected to Meshtastic device")

    def send_private_message(self, to_id, message):
        try:
            self.interface.sendText(message, destinationId=to_id)
            self.logger.info(f"Sent message to {to_id}: {message}")
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")

    def run(self):
        self.logger.info("Bot is running...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Bot shutting down...")
        finally:
            if self.interface:
                self.interface.close()
                self.logger.info("Interface closed")

def main():
    parser = argparse.ArgumentParser(description='Meshtastic Bot')
    parser.add_argument('--connection-type', choices=['serial', 'wifi'], default='serial',
                      help='Connection type (serial or wifi)')
    parser.add_argument('--hostname', help='Hostname for WiFi connection')
    parser.add_argument('--serial-port', help='Serial port path (e.g., /dev/ttyUSB0)')

    args = parser.parse_args()

    try:
        bot = MeshtasticBot(
            connection_type=args.connection_type,
            hostname=args.hostname,
            serial_port=args.serial_port
        )
        bot.run()
    except Exception as e:
        logging.error(f"Bot failed to start: {e}")

if __name__ == "__main__":
        main()
