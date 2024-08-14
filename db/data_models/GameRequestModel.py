class GameRequestForSender:
    def __init__(self, request_id: int, game_id: int, game_name: str, approved: bool = False):
        self.request_id = request_id
        self.game_id = game_id
        self.game_name = game_name
        self.approved = approved

    def __str__(self):
        return (f"Game access request {self.request_id}, for game {self.game_id} - {self.game_name},"
                f" status - {'approved' if self.approved else 'not considered'} ")


class GameRequestForMaster:
    def __init__(self, request_id: int, user_id: int, user_name: str, game_id: int, game_name: str,
                 approved: bool = False):
        self.request_id = request_id
        self.user_id = user_id
        self.user_name = user_name
        self.game_id = game_id
        self.game_name = game_name
        self.approved = approved

    def __str__(self):
        return (f"Game access request {self.request_id}, for game {self.game_id} - {self.game_name},"
                f" from user {self.user_id} - {self.user_name},"
                f" status - {'approved' if self.approved else 'not considered'} ")
