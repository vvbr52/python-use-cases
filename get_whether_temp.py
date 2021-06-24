#user name =vvbr_api
#email_id =vvbr.100@gmail.com
#password ='Arun@452'
#website https://home.openweathermap.org/

#APIkey=82ff7f5515f3e23cc9d9b0e71be46950

import requests

# paste your api key here
api_key = "82ff7f5515f3e23cc9d9b0e71be46950"

# getting city name from user
city = input("Enter city name: ")

data = requests.get(
    f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&APPID={api_key}"
)

# getting the data
print(f"Location: {data.json().get('name')}, {data.json().get('sys').get('country')}")
print(f"Temperature: {data.json().get('main')['temp']}°C")
print(f"Weather: {data.json().get('weather')[0].get('main')}")
print(f"Min/Max Temperature: {data.json().get('main')['temp_min']}°C/{data.json().get('main')['temp_max']}°C")
print(f"Humidity: {data.json().get('main')['humidity']}%")
print(f"Wind: {data.json().get('wind')['speed']} km/h")
