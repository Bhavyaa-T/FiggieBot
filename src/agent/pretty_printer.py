
def print_order_book(order_book: dict):
    """
    Pretty-prints the order book, skipping empty (-1) entries.
    Only prints the header if there is at least one real order.
    """
    if not order_book:
        return

    lines = []

    # Collect bids
    for suit, order in order_book.get("bids", {}).items():
        if order["order_id"] == -1:
            continue
        lines.append(f"🟢 {order['player_id']} bids {suit} @ {order['price']}")

    # Collect offers
    for suit, order in order_book.get("offers", {}).items():
        if order["order_id"] == -1:
            continue
        lines.append(f"🔴 {order['player_id']} offers {suit} @ {order['price']}")

    if lines is not None:  # only print if there are actual orders
        print("📖 Current Order Book:")
        for line in lines:
            print(line)


def print_state(state: dict):
    """
    Prints a message based on the game state received from the server.
    Handles update_game, accept_order, place_order, error, etc.
    Always prints the order book if present.
    """
    if "type" not in state or "data" not in state:
        print(state)
        return

    msg_type = state["type"]
    data = state["data"]

    if msg_type == "error":
        print(f"⚠️ {data['message']}")

    elif msg_type == "accept_order":
        accepted = data["accepted_order"]
        buyer = accepted["buyer_id"]
        seller = accepted["seller_id"]
        suit = accepted["suit"]
        price = accepted["price"]
        print(f"💱 Trade executed: {buyer} bought {suit} from {seller} @ {price}")

    elif msg_type == "place_order":
        print(f"📥 New order: {data['message']}")

    else:
        print("📩 Other message:", state)

    # Always show order book if available
    if "order_book" in data:
        print_order_book(data["order_book"])
