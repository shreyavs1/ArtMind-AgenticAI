from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image
import io
import os
import random

app = Flask(__name__, static_folder="static", template_folder="templates")
os.makedirs("static/uploads", exist_ok=True)

# ------------------------------
# Helper: palette extraction
# ------------------------------
def extract_palette_from_pil_image(pil_img, num_colors=5):
    """
    Use Pillow adaptive palette quantization to reduce to num_colors and return hex colors.
    """
    # convert to RGB if not already
    img = pil_img.convert("RGBA")
    # Resize small to speed up quantization
    img = img.copy()
    img.thumbnail((200, 200))
    # Convert to P (palette) with adaptive palette
    paletted = img.convert("P", palette=Image.ADAPTIVE, colors=num_colors)
    palette = paletted.getpalette()  # list of r,g,b...
    color_counts = sorted(paletted.getcolors(), reverse=True)  # (count, index)
    colors = []
    for count, idx in color_counts[:num_colors]:
        r = palette[idx * 3]
        g = palette[idx * 3 + 1]
        b = palette[idx * 3 + 2]
        colors.append('#{:02x}{:02x}{:02x}'.format(r, g, b))
    # if we didn't get enough colors, pad with random from palette set
    while len(colors) < num_colors:
        colors.append("#%06x" % random.randint(0, 0xFFFFFF))
    return colors

# ------------------------------
# Static built palettes and agents
# ------------------------------
BUILT_PALETTES = [
    ["#F6D8AE", "#E6A57E", "#DA627D", "#A53860", "#450920"],
    ["#114B5F", "#1A936F", "#88D498", "#C6DABF", "#F3E9D2"],
    ["#03045E", "#0077B6", "#00B4D8", "#90E0EF", "#CAF0F8"],
    ["#432371", "#714674", "#9F6976", "#C78A76", "#F7A76C"]
]

IDEA_TEMPLATES = [
    lambda t: f"Try painting a {t} scene in an impressionist style — focus on light and shadow.",
    lambda t: f"Explore an abstract representation of '{t}' using flowing brush strokes and bold colors.",
    lambda t: f"How about a minimalistic version of {t} with 3 dominant colors?"
]

GUIDE_TEMPLATES = [
    lambda t: ("1) Start with a rough pencil sketch.\n"
               "2) Block in main colors and shapes.\n"
               "3) Add shadows and highlights to create depth.\n"
               "4) Work on edges and texture.\n"
               "5) Finish with details and signature."),
    lambda t: ("1) Quick tonal study to get values right.\n"
               "2) Lay down base midtones.\n"
               "3) Build forms and transitions.\n"
               "4) Add accents and highlights last.")
]

CRITIC_TEMPLATES = [
    "Your color balance sounds harmonious! Try enhancing contrast between background and subject.",
    "It seems expressive — focus on consistent brush strokes for emotional flow.",
    "Add some warmer tones to balance the cool palette; this will add vibrancy to your piece."
]

# ------------------------------
# Routes
# ------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/inspire", methods=["POST"])
def inspire():
    """
    Accepts JSON or multipart form:
    - 'prompt' (text)
    - optional image file 'image' (multipart/form-data)
    Returns JSON: idea, guide, critic, palette (list)
    """
    prompt_text = request.form.get("prompt") or (request.json and request.json.get("prompt"))
    if not prompt_text:
        return jsonify({"error": "No prompt provided"}), 400

    # Choose idea/guide/critic
    idea = random.choice(IDEA_TEMPLATES)(prompt_text)
    guide = random.choice(GUIDE_TEMPLATES)(prompt_text)
    critic = random.choice(CRITIC_TEMPLATES)

    # If image present, attempt to extract palette
    palette = None
    if "image" in request.files:
        f = request.files["image"]
        if f and f.filename:
            # Save if you want (optional)
            filename = os.path.join("static", "uploads", f.filename)
            f.save(filename)
            try:
                pil_img = Image.open(filename)
                palette = extract_palette_from_pil_image(pil_img, num_colors=5)
            except Exception as e:
                print("Palette extraction failed:", e)
                palette = None

    if not palette:
        palette = random.choice(BUILT_PALETTES)

    return jsonify({
        "idea": idea,
        "guide": guide,
        "critic": critic,
        "palette": palette
    })

# optional: serve uploaded files
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory("static/uploads", filename)

# Run the app
if __name__ == "__main__":
    # Use 127.0.0.1 to avoid IPv6 [::] issues
    app.run(host="127.0.0.1", port=8000, debug=True)
