"""
Script pour initialiser l'authentification Gmail.
Exécutez ce script une seule fois pour créer token.json depuis client_secret.json.
"""

from mail_management import get_credentials

if __name__ == "__main__":
    print("="*60)
    print("Configuration de l'authentification Gmail")
    print("="*60)
    print("\nCe script va ouvrir votre navigateur pour vous connecter à Gmail.")
    print("Acceptez les permissions demandées.\n")
    
    try:
        creds = get_credentials()
        print("\n" + "="*60)
        print("✓ Authentification réussie !")
        print("✓ token.json créé avec succès")
        print("="*60)
        print("\nVous pouvez maintenant utiliser mail_management.py")
    except Exception as e:
        print(f"\n✗ Erreur : {e}")
        import traceback
        traceback.print_exc()

