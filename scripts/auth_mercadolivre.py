import os
import requests
import sys

def main():
    print("=" * 60)
    print("🔑 AUTENTICADOR MERCADO LIVRE OAUTH")
    print("=" * 60)

    client_id = input("Client ID [padrão: 2324141600741014]: ").strip() or "2324141600741014"
    client_secret = input("Secret Key (Client Secret): ").strip()
    code = input("Código de autorização (TG-...): ").strip()
    redirect_uri = "https://httpbin.org/get"

    if not client_secret or not code:
        print("❌ Erro: Secret Key e Código TG são obrigatórios.")
        sys.exit(1)

    print("\nSolicitando Access Token ao Mercado Livre...")
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded"
    }

    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=15)
        data = resp.json()

        if resp.status_code == 200:
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            user_id = data.get("user_id")
            expires_in = data.get("expires_in")

            print("\n✅ Autenticação realizada com sucesso!")
            print(f"👤 Usuário ID: {user_id}")
            print(f"⏱️ Expiração: {expires_in // 3600} horas")

            # Atualiza ou cria o arquivo .env
            env_path = ".env"
            lines = []
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

            token_updated = False
            new_lines = []
            for line in lines:
                if line.startswith("MERCADOLIVRE_ACCESS_TOKEN="):
                    new_lines.append(f"MERCADOLIVRE_ACCESS_TOKEN={access_token}\n")
                    token_updated = True
                else:
                    new_lines.append(line)

            if not token_updated:
                new_lines.append(f"\nMERCADOLIVRE_ACCESS_TOKEN={access_token}\n")

            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            print("💾 Token salvo com sucesso no seu arquivo .env!")
            print("\nVocê já pode executar:")
            print("python main.py --once --query \"Macbook\"")

        else:
            print(f"\n❌ Erro retornado pela API ({resp.status_code}):")
            print(data.get("message") or data)
            print("\nLembre-se: O código 'TG-...' expira em 10 minutos e só pode ser usado uma vez.")
            print("Se expirou, basta abrir novamente o link de autorização no navegador.")

    except Exception as e:
        print(f"\n❌ Falha na requisição: {e}")

if __name__ == "__main__":
    main()
