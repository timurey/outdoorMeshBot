import meshtastic
import meshtastic.serial_interface
import meshtastic.tcp_interface
from pubsub import pub
import time
import argparse

# Import the updated WeatherForecast class from weather.py
from weather import WeatherForecast

class MeshtasticBot:
    def __init__(self, connection_type='serial', hostname=None, serial_port=None):
        """
        Initializes the MeshtasticBot with the specified connection parameters.

        Args:
            connection_type (str): Type of connection ('serial' or 'wifi').
            hostname (str, optional): Hostname for WiFi connection.
            serial_port (str, optional): Serial port path for serial connection.
        """
        self.interface = None
        self.setup_connection(connection_type, hostname, serial_port)
        self.setup_subscribers()

    def setup_connection(self, connection_type, hostname, serial_port):
        """
        Sets up the connection to the Meshtastic device based on the connection type.

        Args:
            connection_type (str): Type of connection ('serial' or 'wifi').
            hostname (str, optional): Hostname for WiFi connection.
            serial_port (str, optional): Serial port path for serial connection.

        Raises:
            ValueError: If required parameters for the connection type are missing.
            Exception: If the connection fails.
        """
        try:
            if connection_type == 'wifi':
                if not hostname:
                    raise ValueError("Hostname is required for WiFi connection")
                print(f"Connecting via WiFi to {hostname}...")
                self.interface = meshtastic.tcp_interface.TCPInterface(hostname=hostname)
            else:  # serial
                if not serial_port:
                    raise ValueError("Serial port is required for serial connection")
                print(f"Connecting via Serial to {serial_port}...")
                self.interface = meshtastic.serial_interface.SerialInterface(devPath=serial_port)
            print("Connection established successfully.")
        except Exception as e:
            print(f"Failed to connect: {e}")
            raise

    def setup_subscribers(self):
        """
        Sets up the subscribers for Meshtastic events.
        """
        pub.subscribe(self.on_receive, "meshtastic.receive")
        pub.subscribe(self.on_connection, "meshtastic.connection.established")

    def on_receive(self, packet, interface):
        """
        Callback function triggered when a message is received.

        Args:
            packet (dict): The received packet data.
            interface: The Meshtastic interface instance.
        """
        try:
            # Check if it's a text message
            if packet.get('decoded', {}).get('portnum') == 'TEXT_MESSAGE_APP':
                message = packet.get('decoded', {}).get('text', '').strip()
                from_id = packet.get('fromId')
                
                print(f"Received message from {from_id}: {message}")
                
                # Handle commands
                if message.startswith('#weather'):
                    self.handle_weather_command(from_id, message)
                elif message == '#test':
                    self.send_private_message(from_id, "Received a test message")
                else:
                    self.send_private_message(from_id, "Unknown command. Available commands: #test, #weather <latitude> <longitude> [hours]")
        except Exception as e:
            print(f"Error processing message: {e}")

    def on_connection(self, interface, topic=pub.AUTO_TOPIC):
        """
        Callback function triggered when a connection is established.

        Args:
            interface: The Meshtastic interface instance.
            topic: The topic of the message.
        """
        print("Connected to Meshtastic device")

    def send_private_message(self, to_id, message):
        """
        Sends a private message to a specific user.

        Args:
            to_id (int): The destination user ID.
            message (str): The message to send.
        """
        try:
            # Meshtastic typically has a limit of around 500 bytes per message
            MAX_PAYLOAD_SIZE = 200  # Adjust based on your device's configuration

            if len(message.encode('utf-8')) <= MAX_PAYLOAD_SIZE:
                self.interface.sendText(message, destinationId=to_id)
                print(f"Sent message to {to_id}: {message[:50]}{'...' if len(message) > 50 else ''}")
            else:
                # Split the message into chunks
                chunks = self.split_message(message, MAX_PAYLOAD_SIZE)
                for chunk in chunks:
                    self.interface.sendText(chunk, destinationId=to_id)
                    print(f"Sent message chunk to {to_id}: {chunk[:50]}{'...' if len(chunk) > 50 else ''}")
                    time.sleep(0.5)  # Slight delay to prevent message collision
        except Exception as e:
            print(f"Error sending message: {e}")

    def split_message(self, message, max_size):
        """
        Splits a long message into smaller chunks based on the maximum size.

        Args:
            message (str): The full message to split.
            max_size (int): The maximum size of each chunk in bytes.

        Returns:
            List[str]: A list of message chunks.
        """
        encoded_message = message.encode('utf-8')
        chunks = []
        start = 0
        while start < len(encoded_message):
            end = start + max_size
            # Ensure we don't split multi-byte characters
            while end < len(encoded_message) and (encoded_message[end] & 0xC0) == 0x80:
                end -= 1
            chunk = encoded_message[start:end].decode('utf-8', errors='ignore')
            chunks.append(chunk)
            start = end
        return chunks

    def handle_weather_command(self, to_id, message):
        """
        Handles the #weather command by fetching and sending weather data.

        Expected command format: #weather <latitude> <longitude> [hours]

        Args:
            to_id (int): The destination user ID.
            message (str): The received message containing the command.
        """
        parts = message.split()
        if len(parts) not in [3, 4]:
            self.send_private_message(to_id, "Usage: #weather <latitude> <longitude> [hours]")
            return

        try:
            latitude = float(parts[1])
            longitude = float(parts[2])
            forecast_hours = 24  # Default value

            if len(parts) == 4:
                forecast_hours = int(parts[3])
                if forecast_hours <= 0:
                    raise ValueError("Forecast hours must be a positive integer.")

            # Optional: Define a maximum forecast hours limit to prevent excessively long messages
            MAX_FORECAST_HOURS = 48
            if forecast_hours > MAX_FORECAST_HOURS:
                forecast_hours = MAX_FORECAST_HOURS
                self.send_private_message(to_id, f"Maximum forecast hours limited to {MAX_FORECAST_HOURS} hours.")

            print(f"Fetching weather for Latitude: {latitude}, Longitude: {longitude}, Hours: {forecast_hours}")

            # Create an instance of WeatherForecast
            weather_forecast = WeatherForecast(latitude=latitude, longitude=longitude)
            weather_forecast.fetch_forecast(forecast_hours=forecast_hours)
            forecasts = weather_forecast.get_forecast(forecast_hours=forecast_hours)

            if not forecasts:
                self.send_private_message(to_id, "No forecast data available for the specified period.")
                return

            # Format the forecast data
            forecast_message = (
                f"🌤 **Weather Forecast for Next {forecast_hours} Hours**\n"
                f"📍 **Location:** {latitude}, {longitude}\n\n"
            )

            for forecast in forecasts:
                forecast_message += (
                    f"🕒 {forecast['time']} | 🌡 {forecast['temperature_2m']}°C | "
                    f"🌧 {forecast['precipitation']}mm | 💨 {forecast['windspeed_10m']}km/h | "
                    f"☁️ {forecast['weather_description']}\n"
                )

            # Send the message
            self.send_private_message(to_id, forecast_message)

        except ValueError as ve:
            self.send_private_message(to_id, f"Invalid input: {ve}")
        except Exception as e:
            self.send_private_message(to_id, f"Error fetching weather data: {e}")

    def run(self):
        """
        Runs the bot, keeping it active and responsive to incoming messages.
        """
        try:
            print("Bot is running. Press Ctrl+C to exit.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nBot shutting down...")
        finally:
            if self.interface:
                self.interface.close()
                print("Connection closed.")

def main():
    """
    The main entry point for the bot. Parses command-line arguments and starts the bot.
    """
    parser = argparse.ArgumentParser(description='Meshtastic Bot with Weather Functionality')
    parser.add_argument('--connection-type', choices=['serial', 'wifi'], default='serial',
                      help='Connection type (serial or wifi). Default is serial.')
    parser.add_argument('--hostname', help='Hostname for WiFi connection.')
    parser.add_argument('--serial-port', help='Serial port path (e.g., /dev/ttyUSB0). Required for serial connection.')
    
    args = parser.parse_args()
    
    # Validate arguments based on connection type
    if args.connection_type == 'wifi' and not args.hostname:
        parser.error("--hostname is required for WiFi connection.")
    if args.connection_type == 'serial' and not args.serial_port:
        parser.error("--serial-port is required for serial connection.")
    
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
