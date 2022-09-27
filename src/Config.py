class Config:
    VIDEO = "fifa.mkv"
    CONFIG = {"fifa.mkv": {"CBT": [(30, 0, 40), (50, 255, 255)],  # Cutting background threshold (getting whole pitch)
                           "PLT": [(0, 110, 0), (255, 255, 255)]},  # Extruding pitch lines threshold (getting pitch lines)
              "lewy.mp4": {"CBT": [(30, 0, 30), (50, 255, 255)],
                           "PLT": [(0, 110, 0), (255, 255, 255)]},
              "v.mp4": {"CBT": [(30, 0, 30), (70, 255, 200)],
                        "PLT": [(0, 120, 0), (255, 255, 255)]}
              }

    @staticmethod
    def get_cutting_background_threshold():
        return Config.CONFIG[Config.VIDEO]["CBT"]

    @staticmethod
    def get_pitch_lines_threshold():
        return Config.CONFIG[Config.VIDEO]["PLT"]

    @staticmethod
    def get_video():
        return Config.VIDEO