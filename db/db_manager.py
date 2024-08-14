import time

import aiosqlite
import asyncio
from db.data_models.GameModels import *
from db.data_models.LocationsModel import *
from db.data_models.GameRequestModel import *
from db.data_models.SessionModel import *
from utils import list_utils

db_path = 'db/database.db'


async def is_user_signup(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
                f"SELECT CASE WHEN EXISTS(SELECT 1 FROM Users WHERE id={user_id}) THEN {True} ELSE {False} END;") as cursor:
            answer = await cursor.fetchone()
        return answer[0] == 1


async def signup_user(user_id: int, name: str):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("INSERT INTO Users (id, name) VALUES (?, ?)", (user_id, name))
        await db.commit()


async def change_user_name(user_id: int, name: str):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"UPDATE Users SET name={name} WHERE id={user_id}")
        await db.commit()


async def create_game(user_id: int, name: str, description: str):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("INSERT INTO Games (master_id, name, description) VALUES (?, ?, ?)",
                         (user_id, name, description))
        await db.commit()


async def get_user_games(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
                f"SELECT * FROM Games WHERE master_id={user_id}") as cursor:
            answer = await cursor.fetchall()
        return list(map(lambda x: GameModelForMaster(game_id=x[0], master=x[1], name=x[2], description=x[3]), answer))


async def update_game_name(game_id: int, name: str):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"UPDATE Games SET name={name} WHERE id={game_id}")
        await db.commit()


async def update_game_description(game_id: int, description: str):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"UPDATE Games SET description={description} WHERE id={game_id}")
        await db.commit()


async def delete_game(game_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"DELETE FROM Games WHERE id={game_id}")
        await db.commit()


async def get_game_locations(game_id: int):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f"SELECT * FROM Locations WHERE game_id={game_id}") as cursor:
            data = await cursor.fetchall()

        answer = []
        added = set()
        parents = dict()
        while True:
            if len(added) == len(data):
                break
            for i in data:
                if i[0] not in added:
                    if i[4] is None:
                        answer.append(GameLocation(location_id=i[0], game_id=i[1], name=i[2], description=i[3]))
                        added.add(i[0])
                        parents.update({i[0]: None})
                    else:
                        if i[4] not in added:
                            continue

                        queue = [i[4]]

                        while True:
                            next_item = parents[queue[0]]
                            if next_item is None:
                                break
                            queue.insert(0, next_item)

                        current_list = answer
                        for j in queue:
                            current_list = list_utils.find_first(current_list,
                                                                 lambda x: x.location_id == j).sub_locations
                        current_list.append(GameLocation(location_id=i[0], game_id=i[1], name=i[2], description=i[3]))
                        added.add(i[0])
                        parents.update({i[0]: i[4]})
        return answer


async def add_game_location(game_id: int, location_name: str, location_description: str, parent_location):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("INSERT INTO Locations (game_id, name, description, parent_location_id) VALUES (?, ?, ?, ?)",
                         (game_id, location_name, location_description, parent_location))
        await db.commit()


async def change_location_name(location_id: int, location_name: str):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"UPDATE Locations SET name={location_name} WHERE id={location_id}")
        await db.commit()


async def change_location_description(location_id: int, location_description: str):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"UPDATE Locations description name={location_description} WHERE id={location_id}")
        await db.commit()


async def delete_location(location_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"DELETE FROM Locations WHERE id={location_id}")
        await db.commit()


async def send_game_request(user_id: int, game_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("INSERT INTO Games_request (user_id, game_id, approved) VALUES (?, ?, ?)",
                         (user_id, game_id, False))
        await db.commit()


async def get_users_games_request(user_id: int, only_approved: bool = False):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f"SELECT Games_request.id, Games_request.game_id, Games.name, Games_request.approved"
                              f" FROM Games_request JOIN Games ON Games.id=Games_request.game_id"
                              f" WHERE Games_request.user_id={user_id}"
                              f" {'AND Games_request.approved != 0' if only_approved else ''}") as cursor:
            data = await cursor.fetchall()
        return list(
            map(lambda x: GameRequestForSender(request_id=x[0], game_id=x[1], game_name=x[2], approved=x[3]), data))


async def get_masters_games_request(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f"SELECT Games_request.id, Users.id, Users.name, Games_request.game_id, Games.name,"
                              f" Games_request.approved FROM Games"
                              f" JOIN Games_request ON Games.id=Games_request.game_id"
                              f" JOIN Users ON Users.id=Games.master_id"
                              f" WHERE Games.master_id={user_id}") as cursor:
            data = await cursor.fetchall()
        return list(map(lambda x: GameRequestForMaster(request_id=x[0], user_id=x[1], user_name=x[2], game_id=x[3],
                                                       game_name=x[4], approved=x[5]), data))


async def approve_request(request_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"UPDATE Games_request SET approved=1 WHERE id={request_id}")
        await db.commit()


async def get_info_about_game(game_id: int):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f"SELECT Games.id, Games.name, Games.description, Users.id, Users.name FROM Games"
                              f" JOIN Users on Users.id=Games.master_id WHERE Games.id={game_id}") as cursor:
            data = await cursor.fetchone()
        if data is None:
            return None
        return GameModelForPlayer(game_id=data[0], name=data[1], description=data[2], master_id=data[3],
                                  master_name=data[4])


async def start_session(game_id: int, password: int, timestamp):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("INSERT INTO Sessions (game_id, started_at, game_progress, password) VALUES (?, ?, ?, ?)",
                         (game_id, timestamp, 0, password))
        await db.commit()


async def join_session(user_id: int, session_id: int, password: int):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f"SELECT password FROM Sessions WHERE game_id={game_id}") as cursor:
            data = await cursor.fetchone()
        if data[0] != password:
            return False
        await db.execute("INSERT INTO Session_connections (user_id, session_id) VALUES (?, ?)",
                         (user_id, session_id))
        await db.commit()
        return True


async def get_user_session(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
                f"""SELECT Sessions.id, Sessions.game_id, Games.name, Sessions.game_progress, 
                Sessions.started_at, "master" AS role
                FROM Sessions JOIN Games ON Games.id=Sessions.game_id
                WHERE Sessions.game_id IN (SELECT id FROM Games WHERE master_id={user_id}) UNION ALL
                SELECT Sessions.id, Sessions.game_id, Games.name, Sessions.game_progress,
                Sessions.started_at, "player" AS role
                FROM Sessions JOIN Games ON Games.id=Sessions.game_id 
                WHERE Sessions.id IN (SELECT session_id FROM Session_connections WHERE user_id={user_id})""") as cursor:
            data = await cursor.fetchone()
        if data is None:
            return None
        return SessionModel(session_id=data[0], game_id=data[1], game_name=data[2], in_progress=bool(data[3]),
                            started_at=data[4], is_master=data[5] == "master")


async def get_users_in_session(session_id: int):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f"SELECT Session_connections.user_id, Users.name FROM Session_connections "
                              f"JOIN Users ON Users.id=Session_connections.user_id "
                              f"WHERE Session_connections.session_id={session_id}") as cursor:
            data = await cursor.fetchall()
        return data


async def leave_session(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"DELETE FROM Session_connections WHERE user_id={user_id}")
        await db.commit()


async def stop_session(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"DELETE FROM Sessions WHERE game_id IN (SELECT id FROM Games WHERE master_id={user_id})")
        await db.commit()


async def block_session(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"UPDATE Sessions SET game_progress=1 "
                         f"WHERE game_id IN (SELECT id FROM Games WHERE master_id={user_id})")
        await db.commit()


async def unblock_session(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"UPDATE Sessions SET game_progress=0 "
                         f"WHERE game_id IN (SELECT id FROM Games WHERE master_id={user_id})")
        await db.commit()


async def get_available_sessions(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(f"""SELECT Sessions.id, Sessions.game_id, Games.name, Sessions.game_progress, 
                              Sessions.started_at
                              FROM Sessions JOIN Games ON Games.id=Sessions.game_id
                              WHERE game_id IN (SELECT game_id FROM Games_request WHERE user_id={user_id} AND approved!=0)
                              AND game_progress=0""") as cursor:
            data = await cursor.fetchall()
        if data is None:
            return None
        return list(map(lambda x: SessionModel(session_id=x[0], game_id=x[1], game_name=x[2], in_progress=bool(x[3]),
                                               started_at=x[4], is_master=False), data))


# async def create_session(user_id: int, session: str):
#     async with aiosqlite.connect(db_path) as db:
#         await db.execute("INSERT INTO users (user_id, session, role) VALUES (?, ?, ?)", (user_id, session, 'master'))
#         await db.commit()
#
#
# async def join_session(user_id: int, session: str):
#     async with aiosqlite.connect(db_path) as db:
#         async with db.execute("SELECT * FROM users WHERE session = ?", (session,)) as cursor:
#             session_exists = await cursor.fetchone()
#         role = 'player' if session_exists else 'master'
#         await db.execute("INSERT INTO users (user_id, session, role) VALUES (?, ?, ?)", (user_id, session, role))
#         await db.commit()
#         return role
#
#
# async def get_role(user_id: int):
#     async with aiosqlite.connect(db_path) as db:
#         async with db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)) as cursor:
#             role = await cursor.fetchone()
#         return role[0] if role else None
#
#
# async def delete_session(session: str):
#     async with aiosqlite.connect(db_path) as db:
#         await db.execute("DELETE FROM users WHERE session = ?", (session,))
#         await db.commit()
#
#
# async def get_sessions():
#     async with aiosqlite.connect(db_path) as db:
#         async with db.execute("SELECT DISTINCT session FROM users") as cursor:
#             sessions = await cursor.fetchall()
#         return [session[0] for session in sessions]
#
#
# async def get_master_session(user_id: int):
#     async with aiosqlite.connect(db_path) as db:
#         async with db.execute("SELECT session FROM users WHERE user_id = ? AND role = 'master'", (user_id,)) as cursor:
#             session = await cursor.fetchone()
#         return session[0] if session else None
#
#
# async def get_session_by_user(user_id: int):
#     async with aiosqlite.connect(db_path) as db:
#         async with db.execute("SELECT session FROM users WHERE user_id = ?", (user_id,)) as cursor:
#             session = await cursor.fetchone()
#         return session[0] if session else None
#
#
# async def leave_session(user_id: int):
#     async with aiosqlite.connect(db_path) as db:
#         await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
#         await db.commit()
#
#
# async def user_has_session(user_id: int):
#     async with aiosqlite.connect(db_path) as db:
#         async with db.execute("SELECT 1 FROM users WHERE user_id = ? AND role = 'master'", (user_id,)) as cursor:
#             return await cursor.fetchone() is not None
#
#
# async def get_users_in_session(session: str):
#     async with aiosqlite.connect(db_path) as db:
#         async with db.execute("SELECT user_id FROM users WHERE session = ?", (session,)) as cursor:
#             users = await cursor.fetchall()
#         return [user[0] for user in users]


def _input_number(number_name: str):
    while True:
        chat_id = input(f"Enter {number_name}: ")
        try:
            chat_id = int(chat_id)
            break
        except:
            print(f"Please enter real {number_name}!")

    return chat_id


def _input_user_id():
    return _input_number("chat_id")


def _input_confirm(text: str = "Confirm"):
    while True:
        inp = input(f'{text} [y/n]: ').lower()
        if inp == 'y':
            return True
        elif inp == 'n':
            return False


def __input_game_id(user_id: int):
    games_list = asyncio.run(get_user_games(user_id))
    print(f"Found {len(games_list)} games\n")
    for index, item in enumerate(games_list):
        print(f"{item.game_id} - {item.name}")
    print("\nChoose game")
    game_id = _input_number("game_id")
    return game_id


if __name__ == "__main__":
    db_path = "database.db"
    while True:
        command = input("Enter command: ")
        if command == "signUp":
            user_id = _input_user_id()
            name = input("Enter user name: ")

            print(f"User with data: chat_id - {user_id}, name - {name}")

            if _input_confirm():
                asyncio.run(signup_user(user_id, name))

        elif command == "userCheck":
            user_id = _input_user_id()
            print("already signUp" if asyncio.run(is_user_signup(user_id))
                  else "need signUp (you can use <signUp> command)")
        elif command == "gameCreate":
            user_id = _input_user_id()
            name = input("Enter game name: ")
            description = input("Enter game description: ")
            print(f"Game with data: user - {user_id}, name - {name}, description - {description}")
            if _input_confirm():
                asyncio.run(create_game(user_id, name, description))
        elif command == "gamesList":
            user_id = _input_user_id()
            games_list = asyncio.run(get_user_games(user_id))
            print(f"Found {len(games_list)} games\n")
            for index, item in enumerate(games_list):
                print(item, "\n")

        elif command == "locationsList":
            user_id = _input_user_id()
            game_id = __input_game_id(user_id)
            locations = asyncio.run(get_game_locations(game_id))
            print(f"Found {len(locations)} locations\n")
            for index, item in enumerate(locations):
                print(item)

        elif command == "locationCreate":
            user_id = _input_user_id()
            game_id = __input_game_id(user_id)
            name = input("Enter location name: ")
            description = input("Enter location description: ")
            parent_loc = None
            if _input_confirm("Is it sub location?"):
                parent_loc = _input_number("parent_loc id")
            print(f"Location with data: game_id - {game_id}, name - {name}, description - {description},"
                  f" parent location - {parent_loc}")
            if _input_confirm():
                asyncio.run(add_game_location(game_id, name, description, parent_loc))

        elif command == "gameRequest":
            user_id = _input_user_id()
            game_id = _input_number("game_id")
            print(f"Game request from {user_id} to game {game_id}")
            print(f"Info about game:")
            print(asyncio.run(get_info_about_game(game_id)))
            if _input_confirm():
                asyncio.run(send_game_request(user_id, game_id))

        elif command == "viewMyRequests":
            user_id = _input_user_id()
            requests_list = asyncio.run(get_users_games_request(user_id))

            print(f"Found {len(requests_list)} requests\n")

            for index, item in enumerate(requests_list):
                print(item, "\n")

        elif command == "viewMyGamesRequests":
            user_id = _input_user_id()
            requests_list = asyncio.run(get_masters_games_request(user_id))

            print(f"Found {len(requests_list)} requests\n")

            for index, item in enumerate(requests_list):
                print(item, "\n")

        elif command == "approveRequest":
            user_id = _input_user_id()
            requests_list = asyncio.run(get_masters_games_request(user_id))

            print(f"Found {len(requests_list)} requests\n")

            for index, item in enumerate(requests_list):
                print(item, "\n")

            print("Choose request")
            request_id = _input_number("request id")
            if _input_confirm("Confirm approving request"):
                asyncio.run(approve_request(request_id))

        elif command == "sessionStart":
            user_id = _input_user_id()
            game_id = __input_game_id(user_id)
            password = _input_number("password")
            if _input_confirm():
                asyncio.run(start_session(game_id, password, time.time()))

        elif command == "sessionStatus":
            user_id = _input_user_id()
            print(asyncio.run(get_user_session(user_id)))

        elif command == "sessionStop":
            user_id = _input_user_id()
            if _input_confirm():
                asyncio.run(stop_session(user_id))

        elif command == "sessionJoin":
            user_id = _input_user_id()
            sessions_list = asyncio.run(get_available_sessions(user_id))
            print(f"Found {len(sessions_list)} sessions\n")
            for index, item in enumerate(sessions_list):
                print(item, "\n")
            print("Choose sessions")
            session_id = _input_number("session_id")
            password = _input_number("password")
            _input_confirm("Confirm join")
            if not asyncio.run(join_session(user_id, session_id, password)):
                print("Error")

        elif command == "sessionBlock":
            user_id = _input_user_id()
            if _input_confirm():
                asyncio.run(block_session(user_id))

        elif command == "sessionUnblock":
            user_id = _input_user_id()
            if _input_confirm():
                asyncio.run(unblock_session(user_id))
        elif command == "sessionLeave":
            user_id = _input_user_id()
            if _input_confirm():
                asyncio.run(leave_session(user_id))
        elif command == "sessionPlayers":
            user_id = _input_user_id()
            print(asyncio.run(get_users_in_session(asyncio.run(get_user_session(user_id)).session_id)))
        elif command == "getAvailableSessions":
            user_id = _input_user_id()
            sessions_list = asyncio.run(get_available_sessions(user_id))
            print(f"Found {len(sessions_list)} sessions\n")
            for index, item in enumerate(sessions_list):
                print(item, "\n")
        else:
            print("command not found")
