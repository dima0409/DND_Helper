class UsersNPC:
    def __init__(self, npc_id: int, game_id: int, game_name: str, name: str, description: str):
        self.npc_id = npc_id
        self.game_id = game_id
        self.game_name = game_name
        self.name = name
        self.description = description

    def __str__(self):
        return f"NPC {self.npc_id} for game {self.game_id} - {self.game_name}, name - {self.name}, description - {self.description}"
