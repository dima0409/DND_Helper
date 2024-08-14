class SessionModel:
    def __init__(self, session_id: int, game_id: int, game_name: str, in_progress: bool, started_at, is_master: bool):
        self.session_id = session_id
        self.game_id = game_id
        self.game_name = game_name
        self.in_progress = in_progress
        self.started_at = started_at
        self.is_master = is_master

    def __str__(self):
        return (f"Session {self.session_id}, "
                f"for game {self.game_id} - {self.game_name}, "
                f"started at - {self.started_at}, "
                f"in progress - {self.in_progress}, "
                f"this player is master - {self.is_master}")
