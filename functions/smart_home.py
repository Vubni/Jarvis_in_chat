import requests, json


def rgb_to_hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = df / mx
    v = mx
    return h, s * 100, v * 100



class Smart_home():
    def __init__(self, access_token) -> None:
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

    def get_devices(self):
        response = requests.get('https://api.iot.yandex.net/v1.0/user/info', headers=self.headers)
        devices = response.json()["devices"]
        for device in devices[:]:
            if "devices.types.smart_speaker" in device["type"]:
                devices.remove(device)
            if "devices.types.light" not in device["type"]:
                devices.remove(device)
        return devices
    

class Lamp_control():
    def __init__(self, access_token, device_id) -> None:
        self.access_token = access_token
        self.device_id = device_id
        self.headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        response = requests.get(f'https://api.iot.yandex.net/v1.0/devices/{self.device_id}', headers=self.headers).json()
        if response["status"] == "error":
            raise "Устройство не найдено"
        self.state = response["state"]
        if self.state == "offline":
            return
        self.capabilities = response["capabilities"]
        self.color = None
        self.color_mode = None
        self.color_scene = None
        self.temperature_k = None
        self.brightness = self.capabilities[0]["state"]["value"]
        self.status = self.capabilities[2]["state"]["value"]

        if self.capabilities[1]["type"] == "devices.capabilities.color_setting":
            if "color_model" in self.capabilities[1]["parameters"]:
                self.color = True
                self.color_mode = self.capabilities[1]["parameters"]["color_model"]
            if "color_scene" in self.capabilities[1]["parameters"]:
                self.color_scene = []
                for j in range(len(self.capabilities[1]["parameters"]["color_scene"]["scenes"])):
                    self.color_scene.append(self.capabilities[1]["parameters"]["color_scene"]["scenes"][j]["id"])
            if "temperature_k" in self.capabilities[1]["parameters"]:
                if self.capabilities[1]["parameters"]["temperature_k"]["min"] != self.capabilities[1]["parameters"]["temperature_k"]["max"]:
                    self.temperature_k = [self.capabilities[1]["parameters"]["temperature_k"]["min"], self.capabilities[1]["parameters"]["temperature_k"]["max"]]

    def turn_on(self):
        self.status = True
        data = {
            "devices": [
                {
                    "id": self.device_id,
                    "actions": [
                        {
                            "type": "devices.capabilities.on_off",
                            "state": {
                                "instance": "on",
                                "value": True
                            }
                        }
                    ]
                }
            ]
        }
        response = requests.post(f'https://api.iot.yandex.net/v1.0/devices/actions', headers=self.headers, data=json.dumps(data)).json()
        return response["status"]
    
    def turn_off(self):
        self.status = False
        data = {
            "devices": [
                {
                    "id": self.device_id,
                    "actions": [
                        {
                            "type": "devices.capabilities.on_off",
                            "state": {
                                "instance": "on",
                                "value": False
                            }
                        }
                    ]
                }
            ]
        }
        response = requests.post(f'https://api.iot.yandex.net/v1.0/devices/actions', headers=self.headers, data=json.dumps(data)).json()
        return response["status"]
    
    def set_brightness(self, value):
        self.brightness = value
        data = {
            "devices": [
                {
                    "id": self.device_id,
                    "actions": [
                        {
                            "type": "devices.capabilities.range",
                            "state": {
                                "instance": "brightness",
                                "value": value
                            }
                        }
                    ]
                }
            ]
        }
        response = requests.post(f'https://api.iot.yandex.net/v1.0/devices/actions', headers=self.headers, data=json.dumps(data)).json()
        return response["status"]
    
    def edit_brightness(self, value):
        self.brightness = self.brightness + value
        data = {
            "devices": [
                {
                    "id": self.device_id,
                    "actions": [
                        {
                            "type": "devices.capabilities.range",
                            "state": {
                                "instance": "brightness",
                                "value": self.brightness + value
                            }
                        }
                    ]
                }
            ]
        }
        response = requests.post(f'https://api.iot.yandex.net/v1.0/devices/actions', headers=self.headers, data=json.dumps(data)).json()
        return response["status"]
    
    def set_scene(self, scene):
        data = {
            "devices": [
                {
                    "id": self.device_id,
                    "actions": [
                        {
                            "type": "devices.capabilities.color_setting",
                            "state": {
                                "instance": "scene",
                                "value": scene
                            }
                        }
                    ]
                }
            ]
        }
        response = requests.post(f'https://api.iot.yandex.net/v1.0/devices/actions', headers=self.headers, data=json.dumps(data)).json()
        return response["status"]
    
    def set_color(self, color_rgb=None, temperature_k=None):
        if not self.color:
            return
            
        if temperature_k is not None and self.temperature_k and self.temperature_k[0] != self.temperature_k[1]:
            data = {
            "devices": [
                    {
                        "id": self.device_id,
                        "actions": []
                    }
                ]
            }
            if temperature_k > self.temperature_k[1]:
                data["devices"][0]["actions"].append({
                            "type": "devices.capabilities.color_setting",
                            "state": {
                                "instance": "temperature_k",
                                "value": self.temperature_k[1]
                            }
                        })
            elif temperature_k < self.temperature_k[0]:
                data["devices"][0]["actions"].append({
                            "type": "devices.capabilities.color_setting",
                            "state": {
                                "instance": "temperature_k",
                                "value": self.temperature_k[0]
                            }
                        })
            else:
                data["devices"][0]["actions"].append({
                            "type": "devices.capabilities.color_setting",
                            "state": {
                                "instance": "temperature_k",
                                "value": temperature_k
                            }
                        })
            response = requests.post(f'https://api.iot.yandex.net/v1.0/devices/actions', headers=self.headers, data=json.dumps(data)).json()
            return response
        
        if color_rgb is None:
            return
        
        if color_rgb[0] > 255:
            color_rgb[0] = 255
        if color_rgb[1] > 255:
            color_rgb[1] = 255
        if color_rgb[2] > 255:
            color_rgb[2] = 255
        if color_rgb[0] < 0:
            color_rgb[0] = 0
        if color_rgb[1] < 0:
            color_rgb[1] = 0
        if color_rgb[2] < 0:
            color_rgb[2] = 0

        if self.color_mode == "hsv":
            h, s, v = rgb_to_hsv(color_rgb[0], color_rgb[1], color_rgb[2])
            data = {
            "devices": [
                    {
                        "id": self.device_id,
                        "actions": [
                            {
                                "type": "devices.capabilities.color_setting",
                                "state": {
                                    "instance": "hsv",
                                    "value": {
                                        "h": int(h),
                                        "s": int(s),
                                        "v": int(v)
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
            response = requests.post(f'https://api.iot.yandex.net/v1.0/devices/actions', headers=self.headers, data=json.dumps(data)).json()
            return response
        else:
            data = {
            "devices": [
                    {
                        "id": self.device_id,
                        "actions": [
                            {
                                "type": "devices.capabilities.color_setting",
                                "state": {
                                    "instance": "rgb",
                                    "value": (color_rgb[0] << 16) + (color_rgb[1] << 8) + color_rgb[2]
                                }
                            }
                        ]
                    }
                ]
            }
            response = requests.post(f'https://api.iot.yandex.net/v1.0/devices/actions', headers=self.headers, data=json.dumps(data)).json()
            return response
            
        

    


# test = Smart_home("y0_AgAAAAAAe1nfAAxa4QAAAAEPVSWkAAAdoC9tjPZFrZVbuk7Q4EfyBeCjVg")
# lamp = Lamp_control("y0_AgAAAAAAe1nfAAxa4QAAAAEPVSWkAAAdoC9tjPZFrZVbuk7Q4EfyBeCjVg", test.get_devices()[1]["id"])