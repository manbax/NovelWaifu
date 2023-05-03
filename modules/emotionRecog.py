
from transformers import pipeline


def emotion_recognition(text):
    emotion_pipeline = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=1)
    emotion_labels = emotion_pipeline(text)
    return emotion_labels[0][0]['label']

if __name__ == '__main__':
    text = "This is very frustrating."
    try:
        emotion_labels = emotion_recognition(text)
        print("Recognized emotions:", emotion_labels)
    except Exception as e:
        print("Error occurred while processing the text:", e)