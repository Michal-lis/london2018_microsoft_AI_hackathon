import requests
import matplotlib.pyplot as plt

from matplotlib.patches import Rectangle
from utils import get_subscription_key
from PIL import Image
from io import BytesIO

subscription_key = get_subscription_key("key.txt")
assert subscription_key
vision_base_url = "https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/"
vision_analyze_url = vision_base_url + "analyze"

image_url = "https://upload.wikimedia.org/wikipedia/commons/d/d9/Bill_gates_portrait.jpg"
celebrity_analyze_url = vision_base_url + "models/celebrities/analyze"
print(celebrity_analyze_url)
headers = {'Ocp-Apim-Subscription-Key': subscription_key}
params = {'model': 'celebrities'}
data = {'url': image_url}
response = requests.post(celebrity_analyze_url, headers=headers, params=params, json=data)
response.raise_for_status()

analysis = response.json()
assert analysis["result"]["celebrities"] is not []
celebrity_info = analysis["result"]["celebrities"][0]
celebrity_name = celebrity_info["name"]
celebrity_face = celebrity_info["faceRectangle"]

plt.figure(figsize=(5, 5))

image = Image.open(BytesIO(requests.get(image_url).content))
ax = plt.imshow(image, alpha=0.6)
origin = (celebrity_face["left"], celebrity_face["top"])
p = Rectangle(origin, celebrity_face["width"], celebrity_face["height"],
              fill=False, linewidth=2, color='b')
ax.axes.add_patch(p)
plt.text(origin[0], origin[1], celebrity_name, fontsize=20, weight="bold", va="bottom")
_ = plt.axis("off")
plt.show()
