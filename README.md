# Meshtastic Weather Bot - outdoorMeshBot

The **Meshtastic Weather Bot - outdoorMeshBot** is an open-source Python bot that connects to Meshtastic devices via either **WiFi** or **Serial** connection and responds to user weather requests. By leveraging the **Open-Meteo API**, the bot provides real-time weather forecasts, such as temperature, wind speed, precipitation, and weather conditions, for specific geographical coordinates (latitude and longitude) directly through the Meshtastic mesh network. This allows users to obtain weather information even in remote locations where traditional internet connectivity may be unavailable.

The bot can be customized to suit different use cases, such as providing weather updates for outdoor adventures, remote operations, or just for fun. The bot listens for incoming commands, processes weather requests, and responds with a detailed forecast. It can handle multiple requests at once, ensuring a smooth experience for users in the mesh network.

## Features

- **Real-time Weather Forecasts**: Provides detailed weather data for any geographical location, using the Open-Meteo API.
- **Meshtastic Integration**: Uses Meshtastic mesh network to deliver forecasts as private messages.
- **Supports Two Connection Types**: Can be configured to connect to Meshtastic via **Serial** or **WiFi**.
- **Customizable Forecast Duration**: Users can request weather data for 24 to 48 hours (default is 24 hours).
- **Easy Setup**: The bot is easy to set up and requires minimal configuration.

### Key Commands

- `#weather <latitude> <longitude> [hours]`: Requests a weather forecast for the given latitude and longitude. Optionally, the number of forecast hours (default: 24) can be specified.
- `#test`: Sends a confirmation message that the bot is functioning correctly.

## Installation

### Prerequisites

To run the Meshtastic Weather Bot, you will need the following:

1. **Python 3.x**: The bot is built with Python 3.7 or newer.
2. **Required Python Libraries**:  
   - `meshtastic` — To interface with the Meshtastic device.
   - `pubsub` — To handle asynchronous messaging and events.
   - `requests` — To fetch weather data from the Open-Meteo API.
   - `pytz` — For timezone handling (used to ensure all times are returned in the correct timezone, e.g., UTC+8 for Beijing Time).

Install all dependencies using:

```bash
pip install meshtastic pubsub requests pytz
```

### Setup

1. Clone the repository or download the code.
2. Install the required dependencies by running the above `pip` command.
3. Adjust the configuration in `bot.py` based on your connection type:
   - **For Serial Connection**: Set the correct serial port (e.g., `/dev/ttyUSB0` on Linux, `COM9` on Windows).
   - **For WiFi Connection**: Set the Meshtastic device's hostname (e.g., the IP address of your WiFi device).

## Running the Bot

Once you have installed the necessary dependencies and configured your connection, you can run the bot using the following command:

```bash
python bot.py --connection-type <serial|wifi> --hostname <hostname> --serial-port <serial_port>
```

- **`--connection-type`**: Choose between `serial` (for USB serial connections) or `wifi` (for WiFi-based Meshtastic devices).
- **`--hostname`**: The hostname or IP address of your Meshtastic device (for WiFi connection).
- **`--serial-port`**: The serial port where your Meshtastic device is connected (for Serial connection).

For serial:
```bash
python bot.py --connection-type serial --serial-port COM9
```

or for WiFi:

```bash
python bot.py --connection-type wifi --hostname <hostname>
```

### Example Output

```bash
Received message from !12345678: #weather 27.73568 105.94545
Fetching weather for Latitude: 27.73568, Longitude: 105.94545, Hours: 24
Sent message to !12345678: 🌤 **Weather Forecast for Next 24 Hours**
📍 **Location**: 27.73568, 105.94545

Sent message to !12345678: 🕒 2024-12-06 19:00 | 🌡 19.3°C | 🌧 0.0mm | 💨 10.1km/h
Sent message to !12345678: 🕒 2024-12-06 21:00 | 🌡 17.9°C | 🌧 0.0mm | 💨 5.5km/h
Sent message to !12345678: 🕒 2024-12-06 23:00 | 🌡 17.2°C | 🌧 0.0mm | 💨 4.0km/h
Sent message to !12345678: 🕒 2024-12-07 01:00 | 🌡 16.6°C | 🌧 0.0mm | 💨 5.4km/h
Sent message to !12345678: 🕒 2024-12-07 03:00 | 🌡 16.1°C | 🌧 0.0mm | 💨 7.6km/h
Sent message to !12345678: 🕒 2024-12-07 05:00 | 🌡 15.4°C | 🌧 0.0mm | 💨 7.6km/h
Sent message to !12345678: 🕒 2024-12-07 07:00 | 🌡 15.2°C | 🌧 0.0mm | 💨 4.3km/h
Sent message to !12345678: 🕒 2024-12-07 09:00 | 🌡 16.5°C | 🌧 0.0mm | 💨 7.6km/h
Sent message to !12345678: 🕒 2024-12-07 11:00 | 🌡 18.4°C | 🌧 0.0mm | 💨 12.4km/h
Sent message to !12345678: 🕒 2024-12-07 13:00 | 🌡 20.4°C | 🌧 0.0mm | 💨 10.9km/h
Sent message to !12345678: 🕒 2024-12-07 15:00 | 🌡 21.3°C | 🌧 0.0mm | 💨 13.0km/h
Sent message to !12345678: 🕒 2024-12-07 17:00 | 🌡 20.4°C | 🌧 0.0mm | 💨 14.5km/h
```

In this example, the bot receives a weather request from a user with the ID `!12345678` for the coordinates `27.73568, 105.94545` (which is in Vietnam). The bot then fetches the weather forecast for the next 24 hours and sends the results as private messages to the user.

### Example Command Input

```
#weather 27.73568 105.94545 24
```

- **Latitude**: 27.73568
- **Longitude**: 105.94545
- **Hours**: 24 (optional, defaults to 24 if omitted)

### Example Response Output

```
Sent message to !12345678: 🌤 **Weather Forecast for Next 24 Hours**
📍 **Location**: 27.73568, 105.94545

Sent message to !12345678: 🕒 2024-12-06 19:00 | 🌡 19.3°C | 🌧 0.0mm | 💨 10.1km/h
Sent message to !12345678: 🕒 2024-12-06 21:00 | 🌡 17.9°C | 🌧 0.0mm | 💨 5.5km/h
Sent message to !12345678: 🕒 2024-12-06 23:00 | 🌡 17.2°C | 🌧 0.0mm | 💨 4.0km/h
...
```

In the example above, the bot sends a series of messages containing hourly weather data for the requested location, including temperature (°C), precipitation (mm), and wind speed (km/h). The forecast data is delivered in batches of two forecast entries at a time, with a brief delay between each batch to avoid message overload.

## Code Structure

### `bot.py`

The main script that runs the Meshtastic bot. It handles:
- Connecting to the Meshtastic device (either via serial or WiFi).
- Listening for incoming messages and processing weather-related commands (`#weather`).
- Sending private messages with weather forecasts to the requesting user.

### `weather.py`

The script that fetches weather data from the Open-Meteo API. It includes:
- **WeatherForecast** class for fetching and processing the weather data.
- It supports:
  - **Fetching forecasts** for a specified location (latitude, longitude).
  - **Parsing the forecast response** from the API and formatting it for display.

## License

This project is licensed under the MIT License. Please refer to the [LICENSE](LICENSE) file for more details.

## Contributing

Contributions are welcome! If you find any bugs or would like to add new features, please feel free to fork the repository and create a pull request.

## Acknowledgments

- **Meshtastic**: For providing the mesh network framework and supporting device integration.
- **Open-Meteo API**: For providing reliable, free weather data.