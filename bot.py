import meshtastic
import meshtastic.serial_interface
import meshtastic.tcp_interface
from pubsub import pub
import time
import argparse

class MeshtasticBot:
    def __init__(self, connection_type='serial', hostname=None, serial_port=None):
        self.interface = None
        self.setup_connection(connection_type, hostname, serial_port)
        self.setup_subscribers()

    def setup_connection(self, connection_type, hostname, serial_port):
        try:
            if connection_type == 'wifi':
                if not hostname:
                    raise ValueError("Hostname is required for WiFi connection")
                self.interface = meshtastic.tcp_interface.TCPInterface(hostname=hostname)
            else:  # serial
                self.interface = meshtastic.serial_interface.SerialInterface(devPath=serial_port)
        except Exception as e:
            print(f"Failed to connect: {e}")
            raise

    def setup_subscribers(self):
        pub.subscribe(self.on_receive, "meshtastic.receive")
        pub.subscribe(self.on_connection, "meshtastic.connection.established")

    def on_receive(self, packet, interface):
        try:
            # Check if it's a text message
            if packet.get('decoded', {}).get('portnum') == 'TEXT_MESSAGE_APP':
                message = packet.get('decoded', {}).get('text', '').strip()
                from_id = packet.get('fromId')
                
                # Handle commands
                if message == '#test':
                    self.send_private_message(from_id, "receive a test message")
        except Exception as e:
            print(f"Error processing message: {e}")

    def on_connection(self, interface, topic=pub.AUTO_TOPIC):
        print("Connected to Meshtastic device")

    def send_private_message(self, to_id, message):
        try:
            self.interface.sendText(message, destinationId=to_id)
        except Exception as e:
            print(f"Error sending message: {e}")

    def run(self):
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Bot shutting down...")
        finally:
            if self.interface:
                self.interface.close()

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
        print(f"Bot failed to start: {e}")

if __name__ == "__main__":
    main()