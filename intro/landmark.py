import requests
import matplotlib.pyplot as plt

from utils import get_subscription_key
from PIL import Image
from io import BytesIO

subscription_key = get_subscription_key("key.txt")
assert subscription_key
vision_base_url = "https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/"
vision_analyze_url = vision_base_url + "analyze"

image_url = "https://upload.wikimedia.org/wikipedia/commons/f/f6/Bunker_Hill_Monument_2005.jpg"
landmark_analyze_url = vision_base_url + "models/landmarks/analyze"
print(landmark_analyze_url)
headers  = {'Ocp-Apim-Subscription-Key': subscription_key}
params   = {'model': 'landmarks'}
data     = {'url': image_url}
response = requests.post(landmark_analyze_url, headers=headers, params=params, json=data)
response.raise_for_status()

analysis      = response.json()
assert analysis["result"]["landmarks"] is not []

landmark_name = analysis["result"]["landmarks"][0]["name"].capitalize()
image = Image.open(BytesIO(requests.get(image_url).content))
plt.imshow(image)
plt.axis("off")
_ = plt.title(landmark_name, size="x-large", y=-0.1)
plt.show()