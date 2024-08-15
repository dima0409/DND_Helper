class UsersNPC:
    def __init__(self, game_id: int, game_name: str, name: str, description: str):
        self.game_id = game_id
        self.game_name = game_name
        self.name = name
        self.description = description

    def __str__(self):
        return f"NPC for game {self.game_id} - {self.game_name}, name - {self.name}, description - {self.description}"
