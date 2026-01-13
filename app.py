from flask import Flask, request, jsonify
import os, threading
from gtts import gTTS
from moviepy import (
    AudioFileClip,
    ImageClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips
)
import arabic_reshaper
from bidi.algorithm import get_display
import requests

app = Flask(__name__)
OUTPUT = "final_video.mp4"

def make_scene(text, index):
    tts = gTTS(text=text, lang="ar")
    audio_path = f"audio_{index}.mp3"
    tts.save(audio_path)
    audio = AudioFileClip(audio_path)

    img_url = "https://images.unsplash.com/photo-1522202176988-66273c2fd55f"
    img_path = f"img_{index}.jpg"
    open(img_path, "wb").write(requests.get(img_url).content)

    img = ImageClip(img_path).set_duration(audio.duration)

    reshaped = get_display(arabic_reshaper.reshape(text))
    txt = TextClip(
        reshaped,
        fontsize=48,
        color="white",
        size=(1280, 200),
        method="caption"
    ).set_position(("center", "bottom")).set_duration(audio.duration)

    return CompositeVideoClip([img, txt]).set_audio(audio)

def build_video(scenes):
    clips = [make_scene(scene, i) for i, scene in enumerate(scenes)]
    final = concatenate_videoclips(clips)
    final.write_videofile(
        OUTPUT,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

@app.route("/upload", methods=["POST"])
def upload():
    data = request.json
    scenes = data.get("scenes", [])

    if not scenes:
        return jsonify({"error": "no scenes"}), 400

    threading.Thread(target=build_video, args=(scenes,), daemon=True).start()

    return jsonify({
        "status": "accepted",
        "message": "video generation started"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
