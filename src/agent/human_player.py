# fmt: off
import asyncio
from typing import Tuple
import websockets
import controller
import pretty_printer as pp
from enum import Enum, auto
import sys
sys.path.insert(0, "../")
from util import constants
# fmt: on

"""
HumanPlayer:
- Reads commands from stdin
- Executes them via controller
- Uses pretty_printer for clean, consistent output
"""

uri = "ws://127.0.0.1:8000/ws"


class CmdType(Enum):
    NONE = auto()
    HELP = auto()
    FETCH = auto()
    BID = auto()
    OFFER = auto()
    ACCEPT_BID = auto()
    ACCEPT_OFFER = auto()
    CANCEL_BID = auto()
    CANCEL_OFFER = auto()


class Command:
    def __init__(self, command_type=CmdType.NONE, suit="", price=-1):
        self.command_type = command_type
        self.suit = suit
        self.price = price


class HumanPlayer:
    def __init__(self, start_round):
        self.player_id = "Human Player"
        self.start_round = start_round

    def print_help(self):
        print("Commands:")
        print("help (h)")
        print("fetch (f): fetch the game state from the server")
        print("bid (b): bid <suit> <price> OR b <suit> <price>")
        print("offer (o): offer <suit> <price> OR o <suit> <price>")
        print("accept_bid (ab): accept_bid <suit> OR ab <suit>")
        print("accept_offer (ao): accept_offer <suit> OR ao <suit>")
        print("cancel_bid (cb): cancel_bid <suit> OR cb <suit>")
        print("cancel_offer (co): cancel_offer <suit> OR co <suit>")
        print("suits: hearts (h), clubs (c), spades (s), diamonds (d)")

    def parse_suit(self, suit_str: str) -> Tuple[bool, str]:
        suit_str = suit_str.lower()
        if suit_str in ("hearts", "h"):
            return True, constants.HEARTS
        if suit_str in ("clubs", "c"):
            return True, constants.CLUBS
        if suit_str in ("spades", "s"):
            return True, constants.SPADES
        if suit_str in ("diamonds", "d"):
            return True, constants.DIAMONDS
        return False, constants.HEARTS

    def parse_cmd(self, cmd_str: str) -> Tuple[bool, Command]:
        cmd_str = cmd_str.strip().lower()
        cmd_lst = cmd_str.split()
        if not cmd_lst:
            return False, Command()

        cmd = cmd_lst[0]
        if cmd in ("help", "h"):
            return True, Command(CmdType.HELP)
        if cmd in ("fetch", "f"):
            return True, Command(CmdType.FETCH)

        if cmd in ("bid", "b") and len(cmd_lst) == 3:
            suit_ok, suit = self.parse_suit(cmd_lst[1])
            return suit_ok, Command(CmdType.BID, suit, int(cmd_lst[2]))

        if cmd in ("offer", "o") and len(cmd_lst) == 3:
            suit_ok, suit = self.parse_suit(cmd_lst[1])
            return suit_ok, Command(CmdType.OFFER, suit, int(cmd_lst[2]))

        if cmd in ("accept_bid", "ab") and len(cmd_lst) == 2:
            suit_ok, suit = self.parse_suit(cmd_lst[1])
            return suit_ok, Command(CmdType.ACCEPT_BID, suit)

        if cmd in ("accept_offer", "ao") and len(cmd_lst) == 2:
            suit_ok, suit = self.parse_suit(cmd_lst[1])
            return suit_ok, Command(CmdType.ACCEPT_OFFER, suit)

        if cmd in ("cancel_bid", "cb") and len(cmd_lst) == 2:
            suit_ok, suit = self.parse_suit(cmd_lst[1])
            return suit_ok, Command(CmdType.CANCEL_BID, suit)

        if cmd in ("cancel_offer", "co") and len(cmd_lst) == 2:
            suit_ok, suit = self.parse_suit(cmd_lst[1])
            return suit_ok, Command(CmdType.CANCEL_OFFER, suit)

        return False, Command()

    async def run_cmd(self, websocket, cmd: Command):
        if cmd.command_type == CmdType.HELP:
            self.print_help()
        elif cmd.command_type == CmdType.FETCH:
            game_state = await controller.get_game_update(websocket)
            pp.print_state(game_state)
        elif cmd.command_type == CmdType.BID:
            await controller.place_bid(websocket, self.player_id, cmd.suit, cmd.price)
        elif cmd.command_type == CmdType.OFFER:
            await controller.place_offer(websocket, self.player_id, cmd.suit, cmd.price)
        elif cmd.command_type == CmdType.ACCEPT_BID:
            await controller.accept_bid(websocket, self.player_id, cmd.suit)
        elif cmd.command_type == CmdType.ACCEPT_OFFER:
            await controller.accept_offer(websocket, self.player_id, cmd.suit)
        elif cmd.command_type == CmdType.CANCEL_BID:
            await controller.cancel_bid(websocket, self.player_id, cmd.suit)
        elif cmd.command_type == CmdType.CANCEL_OFFER:
            await controller.cancel_offer(websocket, self.player_id, cmd.suit)

        # After executing a command, fetch and print the new state
        game_state = await controller.get_game_update(websocket)
        pp.print_state(game_state)

    async def run(self):
        async with websockets.connect(uri) as websocket:
            name = input("Enter your username: ")
            self.player_id += " " + name
            await controller.add_player(websocket, self.player_id)

            if self.start_round:
                await controller.start_round(websocket)

            self.print_help()

            while not await controller.round_started(websocket):
                await asyncio.sleep(0.5)

            while True:
                cmd_str = input("Make an action (type h or help for help): ")
                cmd_ok, cmd = self.parse_cmd(cmd_str)
                while not cmd_ok:
                    print("The command you entered is malformed.")
                    cmd_str = input("Make an action (type h or help for help): ")
                    cmd_ok, cmd = self.parse_cmd(cmd_str)
                await self.run_cmd(websocket, cmd)


if __name__ == "__main__":
    human_player = HumanPlayer(start_round=True)
    asyncio.run(human_player.run())
