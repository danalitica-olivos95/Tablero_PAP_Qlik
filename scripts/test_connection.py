"""Prueba rápida de conexión a Qlik Sense Server."""
import asyncio
import sys
sys.path.insert(0, "src")

from qlik_mcp.qrs_client import QRSClient

async def main():
    print("Probando conexión QRS API...")
    try:
        qrs = QRSClient()
        apps = await qrs.list_apps()
        print(f"OK Conexion exitosa. Apps encontradas: {len(apps)}")
        for a in apps[:5]:
            print(f"  - [{a['id']}] {a['name']} ({a['stream']})")
        if len(apps) > 5:
            print(f"  ... y {len(apps)-5} mas")
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nVerifica:")
        print("  1. Los certificados en certs/ son correctos")
        print("  2. El puerto 4242 es accesible desde tu máquina")
        print("  3. QLIK_USER_DIR y QLIK_USER_ID son correctos en .env o mcp.json")

asyncio.run(main())
