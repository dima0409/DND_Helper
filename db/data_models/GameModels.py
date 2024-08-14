class GameModelForMaster:
    def __init__(self, game_id: int, master: int, name: str, description: str):
        self.game_id = game_id
        self.master = master
        self.name = name
        self.description = description

    def __str__(self):
        return (f"Id: {self.game_id}\n"
                f"MasterId: {self.master}\n"
                f"Game name: {self.name}\n"
                f"Game Description: {self.description}")


class GameModelForPlayer:
    def __init__(self, game_id: int, master_id: int, master_name: int, name: str, description: str):
        self.game_id = game_id
        self.master = master_id
        self.name = name
        self.description = description

    def __str__(self):
        return (f"Id: {self.game_id}\n"
                f"MasterId: {self.master}\n"
                f"MasterName: {self.master}\n"
                f"Game name: {self.name}\n"
                f"Game Description: {self.description}")
