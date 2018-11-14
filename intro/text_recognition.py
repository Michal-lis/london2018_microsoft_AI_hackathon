import requests
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from utils import get_subscription_key
from PIL import Image
from io import BytesIO
import time

subscription_key = get_subscription_key("key.txt")
assert subscription_key

image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Cursive_Writing_on_Notebook_paper.jpg/800px-Cursive_Writing_on_Notebook_paper.jpg"

vision_base_url = "https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/"
text_recognition_url = vision_base_url + "recognizeText"
print(text_recognition_url)

headers = {'Ocp-Apim-Subscription-Key': subscription_key}
params = {'mode': 'Handwritten'}
data = {'url': image_url}
response = requests.post(text_recognition_url, headers=headers, params=params, json=data)
response.raise_for_status()

operation_url = response.headers["Operation-Location"]

analysis = {}
while not "recognitionResult" in analysis:
    response_final = requests.get(response.headers["Operation-Location"], headers=headers)
    analysis = response_final.json()
    time.sleep(1)

polygons = [(line["boundingBox"], line["text"]) for line in analysis["recognitionResult"]["lines"]]

for line in polygons:
    print(line[1])

plt.figure(figsize=(15, 15))

image = Image.open(BytesIO(requests.get(image_url).content))
ax = plt.imshow(image)
for polygon in polygons:
    vertices = [(polygon[0][i], polygon[0][i + 1]) for i in range(0, len(polygon[0]), 2)]
    text = polygon[1]
    patch = Polygon(vertices, closed=True, fill=False, linewidth=2, color='y')
    ax.axes.add_patch(patch)
    plt.text(vertices[0][0], vertices[0][1], text, fontsize=20, va="top")
_ = plt.axis("off")
plt.show()
