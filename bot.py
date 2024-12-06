import meshtastic
import meshtastic.serial_interface
import meshtastic.tcp_interface
from pubsub import pub
import time
import argparse

# Import the WeatherForecast class from weather.py
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
                    self.send_private_message(from_id, "Unknown command. Available commands: #test, #weather <latitude> <longitude>")
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
            self.interface.sendText(message, destinationId=to_id)
            print(f"Sent message to {to_id}: {message[:50]}{'...' if len(message) > 50 else ''}")
        except Exception as e:
            print(f"Error sending message: {e}")

    def handle_weather_command(self, to_id, message):
        """
        Handles the #weather command by fetching and sending weather data.

        Expected command format: #weather <latitude> <longitude>

        Args:
            to_id (int): The destination user ID.
            message (str): The received message containing the command.
        """
        parts = message.split()
        if len(parts) != 3:
            self.send_private_message(to_id, "Usage: #weather <latitude> <longitude>")
            return

        try:
            latitude = float(parts[1])
            longitude = float(parts[2])

            print(f"Fetching weather for Latitude: {latitude}, Longitude: {longitude}")

            # Create an instance of WeatherForecast
            weather_forecast = WeatherForecast(latitude=latitude, longitude=longitude)
            weather_forecast.fetch_forecast()
            forecasts = weather_forecast.get_next_24_hours_forecast()

            if not forecasts:
                self.send_private_message(to_id, "No forecast data available for the next 24 hours.")
                return

            # Format the forecast data
            forecast_message = (
                f"🌤 **Weather Forecast for the Next 24 Hours**\n"
                f"📍 **Location:** {latitude}, {longitude}\n\n"
            )

            for forecast in forecasts:
                forecast_message += (
                    f"🕒 **Time:** {forecast['time']}\n"
                    f"🌡 **Temperature:** {forecast['temperature_2m']}°C\n"
                    f"🌧 **Precipitation:** {forecast['precipitation']} mm\n"
                    f"💨 **Wind Speed:** {forecast['windspeed_10m']} km/h\n"
                    f"🧭 **Wind Direction:** {forecast['winddirection_10m']}°\n"
                    f"☁️ **Condition:** {forecast['weather_description']}\n"
                    "----------------------------------------\n"
                )

            # Optional: Truncate the message if it's too long
            if len(forecast_message) > 2000:
                forecast_message = forecast_message[:1997] + "..."

            self.send_private_message(to_id, forecast_message)

        except ValueError:
            self.send_private_message(to_id, "Invalid latitude or longitude. Please provide numeric values.")
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
