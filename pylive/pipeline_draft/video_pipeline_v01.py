import image_utils
from dataclasses import dataclass

@dataclass
class Video:
    path: str
    seek_position: int=0

# def read_video(file_path, seek:int|None=None):
#     ...

# def time_echo(video, frame, echo:int=5):
#     ...

# def read_video_frame(file_path:str)->image_utils.ImageRGBA:
#     ...



def read_video(file_path:str, frame:int)->image_utils.ImageRGBA:
    return image_utils.read_image(file_path)

def time_offset(video:Video, frame:image_utils.ImageRGBA, offset:int=5)->image_utils.ImageRGBA:
    return frame

def blur(video, size:float):
    return video

def pull(pipeline, context):
    return pipeline


if __name__ == "__main__":
    import rich
    from pathlib import Path
    rich.print("[bold green]Pipeline v0.1[/bold green]")
    rich.print(f"  - {Path.cwd()}")

    [

    ]

    # view
    import cv2
    cv2.imshow("Result", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
