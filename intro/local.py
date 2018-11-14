import requests
import matplotlib.pyplot as plt

from utils import get_subscription_key
from PIL import Image
from io import BytesIO

subscription_key = get_subscription_key("key.txt")
assert subscription_key
vision_base_url = "https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/"
vision_analyze_url = vision_base_url + "analyze"

image_path = "images/politics_as_usual.jpeg"
image_data = open(image_path, "rb").read()
headers = {'Ocp-Apim-Subscription-Key': subscription_key,
           "Content-Type": "application/octet-stream"}
params = {'visualFeatures': 'Categories,Description,Color'}
response = requests.post(vision_analyze_url,
                         headers=headers,
                         params=params,
                         data=image_data)

response.raise_for_status()

analysis = response.json()
image_caption = analysis["description"]["captions"][0]["text"].capitalize()
print(image_caption)

image = Image.open(image_path)
plt.imshow(image)
plt.show()
