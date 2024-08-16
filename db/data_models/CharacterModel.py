class Character:
    def __init__(self, character_id: int, name: str, path: str, owner: int):
        self.character_id = character_id
        self.name = name
        self.path = path
        self.owner = owner

    def __str__(self):
        print(f"{self.character_id} Character {self.name}, Owner - {self.owner}, Path - {self.path}")
