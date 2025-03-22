import os
import json
import requests
import websocket
import csv
import argparse

subs = {}

def subscribe(req, callback):
    subs[str(len(subs) + 1)] = {"req": json.dumps(req), "callback": callback}

def login(phone, pin):
    api = "https://api.traderepublic.com/api/v1/auth/web"
    wss = "wss://api.traderepublic.com"
    headers = {"accept": "*/*", "content-type": "application/json"}
    phone = phone or input("Phone number (+XX...): ")
    pin = pin or input("PIN code: ")
    data = {"phoneNumber": phone, "pin": pin}
    session = requests.Session()
    response = session.post(f"{api}/login", json=data, headers=headers)
    if response.status_code != 200:
        print("Login failed")
        return
    process_id = response.json().get("processId")
    code_2fa = input("2FA code: ")
    response = session.post(f"{api}/login/{process_id}/{code_2fa}")
    if response.status_code != 200:
        print("Login 2FA failed")
        return
    response = session.get(f"{api}/session")
    if response.status_code != 200:
        print("Session failed")
        return
    token = session.cookies.get("tr_session")
    headers = [f"Cookie: tr_session={token}"]
    websocket.WebSocketApp(
        wss,
        header=headers,
        on_open=on_open,
        on_error=on_error,
        on_message=on_message,
    ).run_forever()

def on_open(ws):
    ws.send("connect 31")

def on_error(ws, error):
    print("Error:", error)

def on_message(ws, message):
    parts = message.split(None, 2)
    if parts[0] == "connected":
        for sub_id, sub in subs.items():
            ws.send(f"sub {sub_id} {sub['req']}")
    elif len(parts) > 1 and parts[1] == 'A':
        sub_id = parts[0]
        if sub_id in subs:
            try:
                data = json.loads(parts[2])
                if not subs[sub_id]["callback"](data):
                    del subs[sub_id]
            except Exception as e:
                print(f"Failed: {e}")
    else:
        print(f"Received: {message}")
    if not subs:
        ws.close()

def export_portfolio(data, output_file):
    positions = next((
        c.get("positions", []) for c in data.get("categories", [])
        if c.get("categoryType") == "stocksAndETFs"
    ), [])
    fields = ["name", "isin", "averageBuyIn", "netSize"]
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: p.get(k) for k in fields} for p in positions)
    return False

def main():
    parser = argparse.ArgumentParser(description="Trade Republic Portfolio Downloader")
    parser.add_argument("--phone",   default=os.getenv("TRDL_PHONE"),   help="Phone number")
    parser.add_argument("--pin",     default=os.getenv("TRDL_PIN"),     help="PIN code")
    parser.add_argument("--account", default=os.getenv("TRDL_ACCOUNT"), help="Account number")
    parser.add_argument("--output",  default="output.csv",              help="Output CSV file")
    args = parser.parse_args()
    subscribe({
        "type": "compactPortfolioByType",
        "secAccNo": args.account,
    }, lambda data: export_portfolio(data, args.output))
    try:
        login(args.phone, args.pin)
    except KeyboardInterrupt:
        return

if __name__ == "__main__":
    main()
