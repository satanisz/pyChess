
class Settings:

    def __init__(self):
        self.screen_width, self.screen_height = 1920, 640
        self.scale = 3
        self.piece_width, self.piece_height = int(self.screen_width/self.scale), int(self.screen_height/self.scale)
        self.bg_color = (110, 0, 110) # (225, 225, 225)