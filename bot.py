import meshtastic
import meshtastic.serial_interface
from meshtastic import tcp_interface
from pubsub import pub
import time
import argparse
from weather import WeatherForecast
import re
from datetime import datetime, date

class MeshtasticBot:
    def __init__(self, connection_type='serial', hostname=None, serial_port=None, timezone='Europe/Moscow'):
        self.interface = None
        self.timezone=timezone
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

            comamnd, latitude, longitude, hours, days = self.parse_message(message)

            if comamnd in ('погода', 'прогноз', 'weather', 'forecast'):
                self.handle_weather_command(longitude, latitude, hours, days, from_id)
            elif comamnd in ('помощь', 'help'):
                self.handle_help_command(from_id)
            elif comamnd in ('тест', 'test'):
                self.send_private_message(from_id, f"Тестовое сообщение от nodeId {from_id}")
            elif comamnd in ('пинг', 'ping'):
                self.send_private_message(from_id, "понг")

    def on_connection(self, interface, topic=pub.AUTO_TOPIC):
        print("Connected to Meshtastic device")

    def send_private_message(self, to_id, message):
        self.interface.sendText(message, destinationId=to_id)
        print(f"Sent message to {to_id}: {message[:50]}")

    def handle_weather_command(self,longitude, latitude, hours, days, to_id):

            node_info = self.interface.nodes.get(to_id)
            if longitude == 0 or latitude == 0:
              if node_info and 'position' in node_info:
                  position = node_info['position']
                  if 'latitude' in position and 'longitude' in position:
                      latitude = position['latitude']
                      longitude = position['longitude']
                  else:
                      self.send_private_message(to_id, "Не могу найти ваше местоположение.")
                      time.sleep(5)
                      self.send_private_message(to_id, "Укажите координаты в формате:")
                      time.sleep(5)
                      self.send_private_message(to_id, "#прогноз <широта> <долгота> [Xч | Xд]")
                      time.sleep(5)
                      self.send_private_message(to_id, "например: \"#прогноз 55.44 55.58 3д\"")
                      return
              else:
                self.send_private_message(to_id, "Не могу найти ваше местоположение.")
                time.sleep(5)
                self.send_private_message(to_id, "Укажите координаты в формате:")
                time.sleep(5)
                self.send_private_message(to_id, "#прогноз <широта> <долгота> [Xч | Xд]")
                time.sleep(5)
                self.send_private_message(to_id, "например: \"#прогноз 55.44 55.58 3д\"")
                return
            if hours == 0 and days == 0:
                days = 3

            weather_forecast = WeatherForecast(latitude=latitude, longitude=longitude, timezone=self.timezone)
            weather_forecast.fetch_forecast(hours+days*24)
            if days > 0:
                forecasts = weather_forecast.get_forecast(days*24)
                summary_message = f"Прогноз для {latitude}, {longitude} ({days} дней)"

            elif hours > 0:
                forecasts = weather_forecast.get_forecast(hours)
                summary_message = f"Прогноз для {latitude}, {longitude} ({hours} часов)"

            if not forecasts:
                self.send_private_message(to_id, "No forecast data available.")
                return

            self.send_private_message(to_id, summary_message)

            if days > 0:
                today_date = datetime.strptime(forecasts[0]['time'], '%Y-%m-%d %H:%M')
                min_temp = forecasts[0]['temperature_2m']
                max_temp = forecasts[0]['temperature_2m']
                max_wind = forecasts[0]['windspeed_10m']
                precipitation = forecasts[0]['precipitation']
                for forecast in forecasts:
                  f_date = datetime.strptime(forecast['time'], '%Y-%m-%d %H:%M')
                  if date(today_date.year, today_date.month, today_date.day) == date(f_date.year, f_date.month, f_date.day):
                      min_temp = forecast['temperature_2m'] if forecast['temperature_2m'] < min_temp else min_temp
                      max_temp = forecast['temperature_2m'] if forecast['temperature_2m'] > max_temp else max_temp
                      max_wind = forecast['windspeed_10m'] if forecast['windspeed_10m'] > max_wind else max_wind
                      precipitation += forecast['precipitation']
                      forecast_message = f"📆 {f_date.strftime('%d.%m.%Y')} 🌡 {min_temp}..{max_temp}°C 🌧 {'{:.2f}'.format(precipitation)}mm 💨 {'{:.1f}'.format(max_wind/3.6)}m/s "
                  else:
                    forecast_message = f"📆 {today_date.strftime('%d.%m.%Y')} 🌡 {min_temp}..{max_temp}°C 🌧 {'{:.2f}'.format(precipitation)}mm 💨 {'{:.1f}'.format(max_wind/3.6)}m/s "
                    min_temp = forecast['temperature_2m']
                    max_temp = forecast['temperature_2m']
                    max_wind = forecast['windspeed_10m']
                    precipitation = forecast['precipitation']
                    today_date = datetime.strptime(forecast['time'], '%Y-%m-%d %H:%M')
                    self.send_private_message(to_id, forecast_message)
                    time.sleep(5)
                    forecast_message=""
                if len(forecast_message)>0:
                    self.send_private_message(to_id, forecast_message)
            elif hours >0:
              for forecast in forecasts:
                  f_date = datetime.strptime(forecast['time'], '%Y-%m-%d %H:%M')
                  forecast_message = f"🕒 {f_date.strftime('%d.%m.%Y %H:%M')} 🌡 {forecast['temperature_2m']}°C 🌧 {forecast['precipitation']}mm 💨 {'{:.1f}'.format(forecast['windspeed_10m']/3.6)}m/s"
                  self.send_private_message(to_id, forecast_message)
                  time.sleep(5)


    def handle_help_command(self, to_id):

        node_info = self.interface.nodes.get(to_id)
        if node_info and 'position' in node_info:
            position = node_info['position']
            if 'latitude' in position and 'longitude' in position:
                latitude = position['latitude']
                longitude = position['longitude']
                self.send_private_message(to_id, f"Ваши координаты известны: lat: {latitude} lon: {longitude}")
                time.sleep(5)
                self.send_private_message(to_id, "Можете использовать команду #прогноз [Xч | Xд]")
            else:
                self.send_private_message(to_id, "Не могу найти ваше местоположение.")
                time.sleep(5)
                self.send_private_message(to_id, "Укажите координаты в формате:")
                time.sleep(5)
                self.send_private_message(to_id, "#прогноз <широта> <долгота> [Хч | Xд]")
                time.sleep(5)
                self.send_private_message(to_id, "например: \"#прогноз 55.44 55.58 3д\"")
                return
        else:
                self.send_private_message(to_id, "Не могу найти ваше местоположение.")
                time.sleep(5)
                self.send_private_message(to_id, "Укажите координаты в формате:")
                time.sleep(5)
                self.send_private_message(to_id, "#прогноз <широта> <долгота> [Хч | Xл]")
                time.sleep(5)
                self.send_private_message(to_id, "например: \"#прогноз 55.44 55.58 3д\"")
                return

    def parse_message(self, s):
      pattern = re.compile(r"""(\#(?P<command>\w+)\s*)?                        #command
                            ((?P<lat>\d+[\.\,]?\d*)\s+(?P<lon>\d+[\.\,]?\d*)(\s*))?    #coordinates
                            ((?P<d>\d+)\s*[dд]\s*)?((?P<h>\d+)\s*[hч]\s*)?     #days or hours
                            \s?""", re.VERBOSE)
      match = pattern.match(s)
      command = match.group("command")

      if match.group("lat"):
          lat = float(match.group("lat").replace(',','.'))
      else:
          lat = 0
      if match.group("lon"):
          lon = float(match.group("lon").replace(',','.'))
      else:
          lon=0
      if match.group("h"):
          hours = int(match.group("h"))
      else:
          hours = 0
      if match.group("d"):
          days = int(match.group("d"))
      else:
          days = 0
      return (command, lat, lon, hours, days)

    def run(self):
        print("Bot is running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description='Meshtastic Bot with Weather Functionality')
    parser.add_argument('--connection-type', choices=['serial', 'wifi'], default='serial')
    parser.add_argument('--hostname')
    parser.add_argument('--serial-port')
    parser.add_argument('--timezone', default='Europe/Moscow')  # UTC+3 (Moscow)

    args = parser.parse_args()

    bot = MeshtasticBot(connection_type=args.connection_type, hostname=args.hostname, serial_port=args.serial_port, timezone=args.timezone)
    bot.run()

if __name__ == "__main__":
    main()
