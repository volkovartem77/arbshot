from config import TOKENS


def create_structure():
    structure = []

    for token in TOKENS:
        # Create Structure for Forward
        structure.append(
            (f"USDT-{token}-BTC-USDT", True, f"{token}USDT".lower(), f"{token}BTC".lower(), 'btcusdt')
        )

        # Create Structure for Backward
        structure.append(
            (f"USDT-BTC-{token}-USDT", False, 'btcusdt', f"{token}BTC".lower(), f"{token}USDT".lower())
        )

    return structure
    # return {
    #     "forward": forward,
    #     "backward": backward
    # }
