class AudioManager:

    def __init__(self):
        self.volume = 50
        self.source = "none"
        self.state = "idle"

    def get_status(self):
        return {
            "status": self.state,
            "volume": self.volume,
            "source": self.source
        }