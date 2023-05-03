
import sys
from importlib import util

import pyaudio
import wave

from pathlib import Path
import os
import tarfile
import zipfile
import shutil


def load_module(package_dir):
    package_dir = os.path.abspath(package_dir)
    package_name = os.path.basename(package_dir)

    # Add the parent directory of the package to sys.path
    parent_dir = os.path.dirname(package_dir)
    sys.path.insert(0, parent_dir)

    # Load the package
    spec = util.find_spec(package_name)
    if spec is None:
        raise ImportError(f"Cannot find package '{package_name}'")

    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Remove the parent directory from sys.path
    sys.path.pop(0)

    return module


def extract_tar_gz(file_path, output_dir):
    with tarfile.open(file_path, "r:gz") as tar_file:
        tar_file.extractall(path=output_dir)
    # remove the zip file after extraction
    os.remove(file_path)


def extract_zip(file_path, output_dir):
    with zipfile.ZipFile(file_path, "r") as zip_file:
        zip_file.extractall(path=output_dir)
    # remove the zip file after extraction
    os.remove(file_path)


def move_files(source_dir, target_dir):
    for file_name in os.listdir(source_dir):
        source_path = os.path.join(source_dir, file_name)
        target_path = os.path.join(target_dir, file_name)

        # Check if it's a file
        if os.path.isfile(source_path):
            shutil.move(source_path, target_path)


from pathlib import Path
import os

voicevox_plugin_dir = Path(Path.cwd() / "Plugins" / "voicevox_plugin")
os.makedirs(voicevox_plugin_dir, exist_ok=True)

voicevox_core_python_repository = {
    "CPU": {
        "url": "https://github.com/VOICEVOX/voicevox_core/releases/download/0.14.3/voicevox_core-0.14.3+cpu-cp38-abi3-win_amd64.whl",
        "sha256": "02a3d7359cf4f6c86cc66f5fecf262a7c529ef27bc130063f05facba43bf4006"
    },
    "CUDA": {
        "url": "https://github.com/VOICEVOX/voicevox_core/releases/download/0.14.3/voicevox_core-0.14.3+cuda-cp38-abi3-win_amd64.whl",
        "sha256": "ba987ea728a5fbbea50430737f042924c506849e6e337f95c99895dfc342082e"
    },
    "DIRECTML": {
        "url": "https://github.com/VOICEVOX/voicevox_core/releases/download/0.14.3/voicevox_core-0.14.3+directml-cp38-abi3-win_amd64.whl",
        "sha256": "bf0ac3ad7f1088470e0353ef919d0019eeefc3cf47363d8b293ccf0b3d1732d8"
    }
}
voicevox_core_dll_repository = {
    "CPU": {
        "url": "https://github.com/VOICEVOX/voicevox_core/releases/download/0.14.3/voicevox_core-windows-x64-cpu-0.14.3.zip",
        "sha256": "cf643566b08eb355e00b9b185d25f9f681944074f3ba1d9ae32bc04b98c3df50",
        "path": "voicevox_core-windows-x64-cpu-0.14.3"
    },
    "CUDA": {
        "url": "https://github.com/VOICEVOX/voicevox_core/releases/download/0.14.3/voicevox_core-windows-x64-cuda-0.14.3.zip",
        "sha256": "0ecb724e23820c477372584a4c732af1c01bcb49b451c4ad21fb810baafb20ca",
        "path": "voicevox_core-windows-x64-cuda-0.14.3"
    },
    "DIRECTML": {
        "url": "https://github.com/VOICEVOX/voicevox_core/releases/download/0.14.3/voicevox_core-windows-x64-directml-0.14.3.zip",
        "sha256": "a529b26f6ae7c258cff42671955c1ac4c44080137a4090ee6c977557cc648839",
        "path": "voicevox_core-windows-x64-directml-0.14.3"
    }
}
open_jtalk_dict_file = {
    "url": "https://jaist.dl.sourceforge.net/project/open-jtalk/Dictionary/open_jtalk_dic-1.11/open_jtalk_dic_utf_8-1.11.tar.gz",
    "sha256": "33e9cd251bc41aa2bd7ca36f57abbf61eae3543ca25ca892ae345e394cb10549",
    "path": "open_jtalk_dic_utf_8-1.11"
}

pydantic_dependency_module = {
    "url": "https://files.pythonhosted.org/packages/8a/64/db1aafc37fab0dad89e0a27f120a18f2316fca704e9f95096ade47b933ac/pydantic-1.10.7-cp310-cp310-win_amd64.whl",
    "sha256": "a7cd2251439988b413cb0a985c4ed82b6c6aac382dbaff53ae03c4b23a70e80a",
    "path": "pydantic"
}


class VoicevoxTTSPlugin():
    core = None
    sample_rate = 16000
    acceleration_mode = "CPU"
    voicevox_core_module = None
    previous_speaker = None
    
    def init(self):
        import sys
        import shutil
        from importlib import util
        from utils.settings import GetOption
        from utils.downloader import download_thread
        from dotenv import load_dotenv
        
        os.makedirs(Path(voicevox_plugin_dir / self.acceleration_mode), exist_ok=True)

        if not Path(voicevox_plugin_dir / self.acceleration_mode / "voicevox_core" / "__init__.py").is_file():
            download_thread(voicevox_core_python_repository[self.acceleration_mode]["url"], str(Path(voicevox_plugin_dir / self.acceleration_mode).resolve()), voicevox_core_python_repository[self.acceleration_mode]["sha256"])
            extract_zip(str(Path(voicevox_plugin_dir / self.acceleration_mode / os.path.basename(voicevox_core_python_repository[self.acceleration_mode]["url"])).resolve()), str(Path(voicevox_plugin_dir / self.acceleration_mode).resolve()))

        if not Path(voicevox_plugin_dir / self.acceleration_mode / "voicevox_core" / "voicevox_core.lib").is_file():
            download_thread(voicevox_core_dll_repository[self.acceleration_mode]["url"], str(Path(voicevox_plugin_dir / self.acceleration_mode).resolve()), voicevox_core_dll_repository[self.acceleration_mode]["sha256"])
            extract_zip(str(Path(voicevox_plugin_dir / self.acceleration_mode / os.path.basename(voicevox_core_dll_repository[self.acceleration_mode]["url"]))), str(Path(voicevox_plugin_dir / self.acceleration_mode).resolve()))
            # move dll files to voicevox_core directory
            move_files(str(Path(voicevox_plugin_dir / self.acceleration_mode / voicevox_core_dll_repository[self.acceleration_mode]["path"]).resolve()), str(Path(voicevox_plugin_dir / self.acceleration_mode / "voicevox_core").resolve()))
            # delete folder
            shutil.rmtree(Path(voicevox_plugin_dir / self.acceleration_mode / voicevox_core_dll_repository[self.acceleration_mode]["path"]))

        open_jtalk_dict_path = Path(voicevox_plugin_dir / open_jtalk_dict_file["path"])
        if not Path(open_jtalk_dict_path / "sys.dic").is_file():
            download_thread(open_jtalk_dict_file["url"], str(voicevox_plugin_dir.resolve()), open_jtalk_dict_file["sha256"])
            extract_tar_gz(str(voicevox_plugin_dir / os.path.basename(open_jtalk_dict_file["url"])), str(voicevox_plugin_dir.resolve()))

        # load the pydantic module
        if not Path(voicevox_plugin_dir / "pydantic" / "__init__.py").is_file():
            download_thread(pydantic_dependency_module["url"], str(voicevox_plugin_dir.resolve()), pydantic_dependency_module["sha256"])
            extract_zip(str(voicevox_plugin_dir / os.path.basename(pydantic_dependency_module["url"])), str(voicevox_plugin_dir.resolve()))

        pydantic = load_module(str(Path(voicevox_plugin_dir / pydantic_dependency_module["path"]).resolve()))

        # load the voicevox_core module
        if self.voicevox_core_module is None:
            self.voicevox_core_module = load_module(str(Path(voicevox_plugin_dir / self.acceleration_mode / "voicevox_core").resolve()))

        if self.core is None:
            acceleration_mode = "AUTO"
            if self.acceleration_mode == "CPU":
                acceleration_mode = self.voicevox_core_module.AccelerationMode.CPU
            elif self.acceleration_mode == "CUDA" or self.acceleration_mode == "GPU":
                acceleration_mode = self.voicevox_core_module.AccelerationMode.GPU

            self.core = self.voicevox_core_module.VoicevoxCore(
                acceleration_mode=acceleration_mode,
                open_jtalk_dict_dir=str(open_jtalk_dict_path.resolve())
            )

    def __init__(self):
        # Call the init method when an instance is created
        self.init()

    def _play_audio(self, audio, device=None):
        import wave
        import pyaudio
        buff = self._generate_wav_buffer(audio)

    def _play_audio(self, audio, device=None):
        buff = self._generate_wav_buffer(audio)

        # Set chunk size of 1024 samples per data frame
        chunk = 1024

        # Open the sound file
        wf = wave.open(buff, 'rb')

        # Create an interface to PortAudio
        p = pyaudio.PyAudio()

        # Open a .Stream object to write the WAV file to
        # 'output = True' indicates that the sound will be played rather than recorded
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output_device_index=device,
                        output=True)

        # Read data in chunks
        data = wf.readframes(chunk)

        # Play the sound by writing the audio data to the stream
        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(chunk)

        # Close and terminate the stream
        stream.close()
        wf.close()
        p.terminate()

    def predict(self, text, speaker):
        import numpy as np
        if self.previous_speaker != speaker:
            self.core.load_model(speaker)
            self.previous_speaker = speaker

        if len(text.strip()) == 0:
            return np.zeros(0).astype(np.int16)

        audio_query = self.core.audio_query(text, speaker)

        wav = self.core.synthesis(audio_query, speaker)

        return wav

    def play_tts(self, text, speaker_id):
        return self.predict(text, speaker_id)

    def timer(self):
        pass

    def stt(self, text, result_obj):
        from utils.settings import GetOption
        if self.is_enabled(False) and GetOption("tts_answer") and text.strip() != "":
            audio_device = GetOption("device_out_index")
            wav = self.play_tts(text.strip())
            if wav is not None:
                self._play_audio(wav, audio_device)
        return

    def tts(self, text, device_index, speaker_id, websocket_connection=None, download=False, save_locally=False):
        if self.is_enabled(False):
            wav = self.play_tts(text, speaker_id)

            if wav is not None:
                if save_locally:
                    with open("test.wav", "wb") as outfile:
                        outfile.write(wav)
                else:
                    self._play_audio(wav, device_index)
        return
    
    def is_enabled(self, arg):
        # Replace this condition with the actual condition to check if the plugin is enabled
        return True
"""
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    SPEAKER_ID = int(os.getenv('VOICEMEETER_INPUT_ID'))
    plugin = VoicevoxTTSPlugin()
    plugin.tts("おはよう", SPEAKER_ID, 18, None, False)
    # Call other methods as needed

"""
