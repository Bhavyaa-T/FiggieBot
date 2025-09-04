# fmt: off
import asyncio
import websockets
import controller
import random
import sys
sys.path.insert(0, "../")
from util import constants
import pretty_printer as pp
# fmt: on

"""
RandomPlayer:
- Posts random bids/offers
- Accepts at most one bid and one offer per tick
- Clean handling of update_game, place_order, and error messages
"""

uri = "ws://127.0.0.1:8000/ws"


class RandomPlayer:
    def __init__(self, bid_low, bid_high, offer_low, offer_high, start_round):
        self.player_id = "Random Player 2"
        self.bid_low = bid_low
        self.bid_high = bid_high
        self.offer_low = offer_low
        self.offer_high = offer_high
        self.start_round = start_round

    async def run(self):
        try:
            async with websockets.connect(uri) as websocket:
                await controller.add_player(websocket, self.player_id)

                if self.start_round:
                    await controller.start_round(websocket)

                # Wait until round starts
                while not await controller.round_started(websocket):
                    await asyncio.sleep(0.5)

                print("🚀 Round started")

                while True:
                    game_state = await controller.get_game_update(websocket)
                    msg_type = game_state.get("type")

                    pp.print_state(game_state)
            
                    # === Handle update_game messages ===
                    if msg_type == "update_game":
                        data = game_state["data"]
                        order_book = data.get("order_book", {})
                        player_state = data["player"]


                        # ROUND END CHECK
                        time_left = data.get("time", None)
                        if time_left == 0:
                            print("\n🟩 ROUND ENDED")
                            print(f"💰 Final Balance: {player_state['balance']}")
                            print(f"🃏 Final Hand: {player_state['hand']}")
                            break

                        if time_left is not None:
                            print(f"⏳ Time remaining: {time_left} seconds")

                        # === PLACE RANDOM BID / OFFER ===
                        if random.random() > 0.5:
                            suit = random.choice(constants.SUITS)
                            price = random.randint(self.bid_low, self.bid_high)
                            print(f"🟢 Placing bid: {suit} @ {price}")
                            await controller.place_bid(
                                websocket, self.player_id, suit=suit, price=price
                            )
                        else:
                            suit = random.choice(constants.SUITS)
                            price = random.randint(self.offer_low, self.offer_high)
                            print(f"🔴 Placing offer: {suit} @ {price}")
                            await controller.place_offer(
                                websocket, self.player_id, suit=suit, price=price
                            )

                        # === ACCEPT ONE BID & ONE OFFER PER TICK ===
                        if order_book:
                            # Accept one bid (sell if we have the card)
                            for suit, bid in order_book.get("bids", {}).items():
                                if bid["order_id"] != -1 and bid["player_id"] != self.player_id:
                                    if player_state["hand"].get(suit, 0) > 0:
                                        print(f"✅ Selling {suit} @ {bid['price']} to {bid['player_id']}")
                                        await controller.accept_bid(
                                            websocket, self.player_id, suit=suit
                                        )
                                        break  # stop after first accept

                            # Accept one offer (buy if we can afford it)
                            for suit, offer in order_book.get("offers", {}).items():
                                if offer["order_id"] != -1 and offer["player_id"] != self.player_id:
                                    if player_state["balance"] >= offer["price"]:
                                        print(f"✅ Buying {suit} @ {offer['price']} from {offer['player_id']}")
                                        await controller.accept_offer(
                                            websocket, self.player_id, suit=suit
                                        )
                                        break  # stop after first accept

                        await asyncio.sleep(1)


        except websockets.exceptions.ConnectionClosed:
            print("⚠️ WebSocket connection closed unexpectedly.")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


# === Run the bot ===
if __name__ == "__main__":
    random_player = RandomPlayer(
        bid_low=1, bid_high=10, offer_low=5, offer_high=15, start_round=True
    )
    asyncio.run(random_player.run())
