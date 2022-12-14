class Config:
    VIDEO = "v.mp4"

    CONFIG = {"fifa.mkv": {"CBT": [(30, 0, 40), (50, 150, 150)],   # Cutting background threshold (getting whole pitch)
                           "PLT": [(0, 110, 0), (50, 255, 40)],  # Extruding pitch line threshold (getting pitch line)
                           "FPS": 1,                               # Time [ms] we need to wait between frames
                           "BALL_COLOR": (190, 213, 219)},         # Color of the ball
              "lewy.mp4": {"CBT": [(30, 0, 30), (50, 255, 255)],
                           "PLT": [(0, 110, 0), (255, 255, 255)],
                           "FPS": 15,
                           "BALL_COLOR": (190, 213, 219)},
              "v.mp4": {"CBT": [(30, 0, 30), (70, 255, 200)],
                        "PLT": [(0, 120, 0), (255, 255, 255)],
                        "FPS": 15,
                        "BALL_COLOR": (190, 213, 219)}
              }
    TEAM_COLORS = [(255, 255, 255), (0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
    PROJECT_BACKGROUND = "pitch.png"
    output_file = None

    use_display_colors = False

    @staticmethod
    def get_cutting_background_threshold():
        return Config.CONFIG[Config.VIDEO]["CBT"]

    @staticmethod
    def get_pitch_lines_threshold():
        return Config.CONFIG[Config.VIDEO]["PLT"]

    @staticmethod
    def get_FPS():
        return Config.CONFIG[Config.VIDEO]["FPS"]

    @staticmethod
    def get_BALL_COLOR():
        return Config.CONFIG[Config.VIDEO]["BALL_COLOR"]

    @staticmethod
    def get_pitch_graphic():
        return "../" + Config.PROJECT_BACKGROUND

    @staticmethod
    def get_video():
        return Config.VIDEO
