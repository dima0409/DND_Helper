from utils import str_utils


class GameLocation:
    def __init__(self, location_id: int, game_id: int, name: str, description: str, parent_id):
        self.location_id = location_id
        self.game_id = game_id
        self.name = name
        self.description = description
        self.sub_locations = []
        self.parent_id = parent_id

    def add_sub_location(self, sub_location):
        self.sub_locations.append(sub_location)

    def __str__(self, tabs: int = 0):
        answer = ('    '*tabs + f"{self.location_id} Location {self.name}, game - {self.game_id},"
                                f" description - {self.description}\n" +
                  '    '*tabs + f"Sub locations:\n")
        if len(self.sub_locations) == 0:
            answer += '    '*tabs + "-\n"
        else:
            for i in self.sub_locations:
                answer += i.__str__(tabs+1)
        return answer
