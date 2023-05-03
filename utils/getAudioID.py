import sounddevice as sd
import streamlit as st

def get_audio_devices():
    devices = sd.query_devices()
    device_names = []
    for i, device in enumerate(devices):
        device_names.append(f"{i}: {device['name']}")
    return device_names