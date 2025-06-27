import hashlib
import json
import os.path
import shutil
import subprocess
import logging
import time
import cv2
from json import JSONDecodeError
from typing import Union, Optional
import openai
import pytesseract
from pytube import YouTube
from pytube.exceptions import RegexMatchError
from configparser import ConfigParser


class ConfigManager:
    @staticmethod
    def load(section: str = None, option: str = None) -> Union[ConfigParser, str]:
        if (section is None) != (option is None):
            raise SyntaxError("section AND option parameters OR no parameters must be passed to function config()")
        parser = ConfigParser()
        if not os.path.exists("config.ini"):
            shutil.copy("config.example.ini", "config.ini")
        parser.read("config.ini")
        if parser.get("AppSettings", "openai_api_key") != "your_openai_api_key_here":
            openai.api_key = parser.get("AppSettings", "openai_api_key")
        if parser.get("AppSettings", "tesseract_executable") != "your_path_to_tesseract_here":
            pytesseract.pytesseract.tesseract_cmd = fr'{parser.get("AppSettings", "tesseract_executable")}'
        if section is None and option is None:
            return parser
        else:
            return parser.get(section, option)

    @staticmethod
    def update(new_values_dict) -> None:
        config_file = ConfigManager.load()
        for section, section_data in new_values_dict.items():
            if section not in config_file:
                config_file.add_section(section)
            for key, value in section_data.items():
                if isinstance(value, bool) or isinstance(value, int):
                    value = str(value)
                config_file.set(section, key, value)
        with open('config.ini', 'w') as config_file_save:
            config_file.write(config_file_save)

    @staticmethod
    def get_current_settings() -> dict:
        config_file = ConfigManager.load()
        return {
            'AppSettings': {
                'openai_api_key': config_file.get('AppSettings', 'openai_api_key'),
                'ide_executable': config_file.get('AppSettings', 'ide_executable'),
                'tesseract_executable': config_file.get('AppSettings', 'tesseract_executable'),
            },
            'UserSettings': {
                'programming_language': config_file.get('UserSettings', 'programming_language'),
                'output_path': config_file.get('UserSettings', 'capture_output_path'),
                'mute_ui_sounds': config_file.get('UserSettings', 'mute_ui_sounds'),
                'username': config_file.get('UserSettings', 'username'),
            },
            'Features': {
                'use_youtube_downloader': config_file.get('Features', 'use_youtube_downloader')
            }
        }

    @staticmethod
    def extract_form_values(request):
        new_username = str(request.form.get('username'))
        if new_username == '':
            new_username = 'None'
        new_openai_api_key = str(request.form.get('openai_api_key'))
        if new_openai_api_key == '':
            new_openai_api_key = 'your_openai_api_key_here'
        new_programming_language = str(request.form.get('programming_language'))
        ui_sound_enabled = request.form.get('mute_ui_sounds') == 'True'
        new_path_to_ide = str(request.form.get('ide_executable'))
        if new_path_to_ide == '':
            new_path_to_ide = 'your_path_to_ide_here'
        new_path_to_tesseract = str(request.form.get('tesseract_executable'))
        if new_path_to_tesseract == '':
            new_path_to_tesseract = 'your_path_to_tesseract_here'
        new_output_path = str(request.form.get('output_path'))
        if new_output_path == '':
            new_output_path = 'output_path'
        youtube_downloader_enabled = request.form.get('use_youtube_downloader') == 'True'

        return {
            'AppSettings': {
                'openai_api_key': new_openai_api_key,
                'ide_executable': new_path_to_ide,
                'tesseract_executable': new_path_to_tesseract,
            },
            'UserSettings': {
                'programming_language': new_programming_language,
                'output_path': new_output_path,
                'mute_ui_sounds': ui_sound_enabled,
                'username': new_username,
            },
            'Features': {
                'use_youtube_downloader': youtube_downloader_enabled,
            }
        }

    @staticmethod
    def get_setup_progress() -> [str]:
        config_parser = ConfigManager.load()
        setup_progress = []
        if config_parser.get("AppSettings", "tesseract_executable") != "your_path_to_tesseract_here":
            setup_progress.append("tesseract")
        if config_parser.get("AppSettings", "ide_executable") != "your_path_to_ide_here":
            setup_progress.append("ide")
        if config_parser.get("AppSettings", "openai_api_key") != "your_openai_api_key_here":
            setup_progress.append("api")
        if config_parser.get("UserSettings", "username") != "None":
            setup_progress.append("username")
        return setup_progress


class GeneralUtils:
    @staticmethod
    def hash_string(str_input: str) -> str:
        hash_md5 = hashlib.md5()
        hash_md5.update(str_input.encode('utf-8'))
        return hash_md5.hexdigest()

    @staticmethod
    def format_timestamp(seconds: int) -> str:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f'{str(minutes).zfill(2)}:{str(remaining_seconds).zfill(2)}'

    @staticmethod
    def get_file_extension_for_current_language() -> str:
        current_language = ConfigManager.load("UserSettings", "programming_language").lower()
        programming_languages = {
            'python': '.py', 'javascript': '.js', 'java': '.java', 'c': '.c', 'c++': '.h', 'c#': '.cs',
            'ruby': '.rb', 'php': '.php', 'swift': '.swift', 'go': '.go', 'rust': '.rs', 'kotlin': '.kt',
            'typescript': '.ts', 'scala': '.scala', 'objective-c': '.m', 'r': '.r', 'dart': '.dart',
            'lua': '.lua', 'perl': '.pl', 'haskell': '.hs', 'elixir': '.ex', 'shell': '.sh',
            'groovy': '.groovy', 'powershell': '.ps1', 'batch': '.bat', 'erlang': '.erl', 'clojure': '.clj',
            'elm': '.elm', 'julia': '.jl', 'f#': '.fs', 'fortran': '.f', 'pascal': '.pas', 'ocaml': '.ml',
            'matlab': '.m', 'sql': '.sql', 'pl/sql': '.pls', 'assembly': '.asm', 'vb.net': '.vb',
            'lisp': '.lisp', 'scheme': '.scm', 'ada': '.ada', 'cobol': '.cbl', 'd': '.d', 'tcl': '.tcl',
            'awk': '.awk', 'xml': '.xml', 'json': '.json', 'yaml': '.yml', 'html': '.html', 'css': '.css',
            'sass': '.sass', 'less': '.less', 'markdown': '.md', 'latex': '.tex'
        }
        return programming_languages.get(current_language, ".txt")
    

class FileManager:
    @staticmethod
    def write_to_file(content: str, file_path: str) -> Union[str, None]:
        try:
            with open(file_path, 'w') as file:
                file.write(content)
            logging.info(f"Data successfully written to {file_path}")
            return file_path
        except Exception as error:
            logging.error(error)
            return None

    @staticmethod
    def read_from_file(file_path: str) -> Union[str, None]:
        try:
            with open(file_path, "r") as file:
                data = file.read()
            if data != "":
                return data
        except Exception as error:
            logging.error(error)
        return None

    @staticmethod
    def read_user_data() -> Optional[dict]:
        if not os.path.exists("data/userdata.json"):
            if not os.path.exists("data/"):
                os.makedirs("data/")
            with open("data/userdata.json", "w") as user_data:
                user_data.write(json.dumps({"all_videos": []}))
            return None
        try:
            with open("data/userdata.json", "r") as user_data_json:
                data = json.load(user_data_json)
                return data
        except JSONDecodeError:
            logging.error("Failed to read data from userdata.json, file may be empty.")
            return None


class VideoManager:
    @staticmethod
    def hash_video_file(filename: str) -> str:
        hash_md5 = hashlib.md5()
        with open(f"{VideoManager.get_vid_save_path()}{filename}", "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def get_vid_save_path() -> str:
        vid_download_path = ConfigManager.load("UserSettings", "video_save_path")
        if vid_download_path == "output_path":
            default_path = os.path.dirname(os.getcwd()) + "/out/videos/"
            if not os.path.exists(default_path):
                os.makedirs(default_path)
            return default_path
        if not vid_download_path.endswith("/"):
            vid_download_path += "/"
        return vid_download_path

    @staticmethod
    def get_output_path() -> str:
        output_path = ConfigManager.load("UserSettings", "capture_output_path")
        if output_path == "output_path":
            default_path = os.path.dirname(os.getcwd()) + "/out/"
            if not os.path.exists(default_path):
                os.makedirs(default_path)
            return default_path
        if not output_path.endswith("/"):
            output_path += "/"
        return output_path

    @staticmethod
    def send_code_snippet_to_ide(filename: str, code_snippet: str) -> bool:
        file_path = FileManager.write_to_file(
            code_snippet,
            file_path=f"{VideoManager.get_output_path()}"
                      f"{os.path.splitext(filename.replace(' ', '_'))[0]}"
                      f"{GeneralUtils.get_file_extension_for_current_language()}"
        )
        if file_path is None:
            return False
        try:
            subprocess.run([ConfigManager.load("AppSettings", "ide_executable"), file_path], shell=True)
            logging.info("Successfully opened code snippet in IDE")
            return True
        except subprocess.SubprocessError as error:
            logging.error(error)
            return False

    @staticmethod
    def get_video_data(filename: str) -> Optional[dict]:
        user_data = FileManager.read_user_data()
        if user_data is None:
            return None
        for current_video in user_data["all_videos"]:
            if current_video["filename"] == filename:
                current_video["video_length"] = GeneralUtils.format_timestamp(current_video["video_length"])
                for current_capture in current_video["captures"]:
                    current_capture["timestamp"] = GeneralUtils.format_timestamp(current_capture["timestamp"])
                return current_video
        return None

    @staticmethod
    def is_video_downloaded(filename: str) -> Optional[bool]:
        current_video = VideoManager.get_video_data(filename)
        if current_video is None:
            return None
        if "youtube_url" not in current_video:
            return False
        return True

    @staticmethod
    def update_user_video_data(filename: str, progress: Optional[float] = None, capture: Optional[dict] = None) -> None:
        user_data = FileManager.read_user_data()
        if user_data is None:
            return
        for record in user_data["all_videos"]:
            if record["filename"] == filename:
                if progress is not None:
                    record["progress"] = round(progress)
                if capture is not None:
                    record["captures"].append(capture)
        with open("data/userdata.json", "w") as json_data:
            json.dump(user_data, json_data, indent=4)

    @staticmethod
    def add_video_to_user_data(filename: str, video_title: str, video_hash: str, youtube_url: str = None) -> None:
        user_data = FileManager.read_user_data()
        if user_data is None:
            return
        video_capture = cv2.VideoCapture(f'{VideoManager.get_vid_save_path()}{filename}')
        if not video_capture.isOpened():
            logging.error(f"Failed to open video capture for {filename}")
            return
        middle_frame = round(video_capture.get(cv2.CAP_PROP_FRAME_COUNT) / 2)
        video_capture.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        ret, frame = video_capture.read()
        if not ret:
            logging.error(f"Could not capture frame from video {filename}")
            video_capture.release()
            return
        thumbnail = str(int(time.time())) + ".png"
        if not os.path.exists("static/img"):
            os.makedirs("static/img")
        cv2.imwrite(f"static/img/{thumbnail}", frame)
        new_video = {
            "video_hash": video_hash,
            "filename": filename,
            "alias": video_title,
            "thumbnail": thumbnail,
            "video_length": round(video_capture.get(cv2.CAP_PROP_FRAME_COUNT) / video_capture.get(cv2.CAP_PROP_FPS)),
            "progress": 0,
            "captures": [],
        }
        if youtube_url is not None:
            new_video["youtube_url"] = youtube_url
        video_capture.release()
        user_data["all_videos"].append(new_video)
        with open("data/userdata.json", "w") as json_data:
            json.dump(user_data, json_data, indent=4)

    @staticmethod
    def file_already_exists(video_hash: str) -> bool:
        user_data = FileManager.read_user_data()
        if user_data is None:
            return False
        for record in user_data["all_videos"]:
            if record["video_hash"] == video_hash:
                return True
        return False

    @staticmethod
    def parse_video_data() -> dict:
        user_data = FileManager.read_user_data()
        if user_data is not None:
            continue_watching = []
            all_videos = user_data["all_videos"]
            for current_video in all_videos:
                if current_video["progress"] < current_video["video_length"]:
                    current_video["progress_percent"] = \
                        round((current_video["progress"] / current_video["video_length"]) * 100)
                    current_video["progress"] = GeneralUtils.format_timestamp(current_video["progress"])
                    continue_watching.append(current_video)
                current_video["video_length"] = GeneralUtils.format_timestamp(current_video["video_length"])
        else:
            continue_watching = None
            all_videos = None
        return {
            "all_videos": all_videos,
            "continue_watching": continue_watching
        }

    @staticmethod
    def download_youtube_video(video_url: str) -> str:
        try:
            yt_video = YouTube(video_url)
            yt_stream = yt_video.streams.filter(res="720p", mime_type="video/mp4", progressive=True).first()
            if yt_stream:
                yt_filename = VideoManager.format_youtube_video_name(yt_stream.default_filename)
                yt_stream.download(output_path=VideoManager.get_vid_save_path(), filename=yt_filename)
                filename = yt_filename
                file_hash = VideoManager.hash_video_file(filename)
                if VideoManager.file_already_exists(file_hash):
                    return f"/play_video/{filename}"
                VideoManager.add_video_to_user_data(filename, filename, file_hash, youtube_url=video_url)
                return f"/play_video/{filename}"
        except RegexMatchError as error:
            logging.error(f"Failed to download from youtube with error: {error}")
        return "/upload"

    @staticmethod
    def format_youtube_video_name(filename: str) -> Union[str, None]:
        if filename is None:
            return None
        file_extension = ""
        if "." in filename:
            file_extension = filename[filename.rindex("."):].strip()
            filename = filename.replace(file_extension, "")
        while True:
            if "  " in filename:
                filename = filename.replace("  ", " ")
            else:
                return f"{filename.strip().replace(' ', '_')}{file_extension}"

    @staticmethod
    def filename_exists_in_userdata(filename: str) -> bool:
        user_data = FileManager.read_user_data()
        if user_data is None:
            return False
        all_videos = user_data["all_videos"]
        for current_video in all_videos:
            if current_video["filename"] == filename:
                return True
        return False

    @staticmethod
    def delete_video_from_userdata(filename: str) -> None:
        user_data = FileManager.read_user_data()
        if user_data is None:
            return
        all_videos = user_data["all_videos"]
        for current_video in all_videos:
            if current_video["filename"] == filename:
                all_videos.remove(current_video)
                break
        with open("data/userdata.json", "w") as json_data:
            json.dump(user_data, json_data, indent=4)
