from enum import Enum

class ErrorCode(Enum):
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500

class ErrorMessage(Enum):
    BAD_REQUEST = "bad_request"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    INTERNAL_SERVER_ERROR = "internal_server_error"

class TranscriptionConstants(Enum):
    SAMPLE_RATE = 1600
    BASE_MODLE_VERSION = "ivrit-ai/whisper-v2-d3-e3"
    BASE_FASTER_WHISPER_MODLE_VERSION = "ivrit-ai/faster-whisper-v2-d3-e3"
    DEFAULT_TASK = "transcribe"
    DEFAULT_LANGUAGE = "he"
    AVAILABLE_TRANSCRIPTION_MODELS = ["ivrit-ai/whisper-v2-d3-e3"]
    AVAILABLE_FASTER_WHISPER_TRANSCRIPTION_MODELS = ["ivrit-ai/faster-whisper-v2-d3-e3"]
    AVAILABLE_TRANSCRIPTION_TASK = ["translate","transcribe"]
    AVAILABLE_TRANSCRIPTION_LANGUAGE = ["he","en"]
    TRANSCRIPTION_MDOES = ["online","offline"]


class ErrorMessages(Enum):
    NOT_A_DICT = "Request is not a dictionary."
    MISSING_KEY = "Missing required key: {}"
    INVALID_TASK = "Invalid task."
    INVALID_LANGUAGE = "Invalid language code."
    INVALID_MODEL = "Invalid transcription model."
    INVALID_MODE = "Invalid transcription mode."
    INVALID_CHANNEL = "Invalid channel number. Must be an integer greater than 1."


class OutputPaths(Enum):
    OUTPUT_MERGE_BUCKET = "transcription_microservice/app/services/merge_conversations/"


class GoogleCloudConstants(Enum):
    BUCKET_NAME = "kal-sense-audio-test"
    AUDIO_FOLDER = "audio-to transcribe"
    CONVERSATION_FOLDER = "conversations-output-data"
    SERVICE_ACCOUNT_PATH = "transcription-microservice/kal-sense-qa.json"

class LoclStorgeConstants(Enum):
    OUTPUT_FOLDER = "/Users/eliordana/Desktop/local_storge"




class TempDirPath(Enum):
    TEMP_OUTPUT_SEAPARATE_AUDIO_DIR = "transcription_microservice/app/services/separate_audio_channels_output"
    TEMP_OUTPUT_TRANSCRIPT_PATH = "transcription_microservice/app/services/transcript_output_separate_audio_channels"

class ValidMessages(Enum):
    REQUEST_VAILD = "Request is valid"



class GlobalConstant(Enum):
    AUDIO_EXTENSIONS = ['.wav', '.mp3','.ogg']