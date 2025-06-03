#!/usr/bin/env python3
"""
Script para generar secrets seguros para cada entorno
"""
import secrets
import string
import json
import os

def generate_secret_key(length=50):
    """Genera una SECRET_KEY segura para Django"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(chars) for _ in range(length))

def generate_password(length=20):
    """Genera una contraseña segura"""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))

def main():
    environments = ['development', 'staging', 'production']
    
    for env in environments:
        print(f"\n🔐 Generando secrets para {env.upper()}:")
        
        secrets_dict = {
            'SECRET_KEY': generate_secret_key(),
            'DB_PASSWORD': generate_password(),
            'REDIS_PASSWORD': generate_password(),
            'ADMIN_PASSWORD': generate_password(),
        }
        
        # Guardar en archivo
        filename = f'.env.{env}.secrets'
        with open(filename, 'w') as f:
            for key, value in secrets_dict.items():
                f.write(f"{key}={value}\n")
        
        print(f"✅ Secrets guardados en {filename}")
        
        # Mostrar en pantalla (solo para desarrollo)
        if env == 'development':
            print("\nSecrets generados:")
            for key, value in secrets_dict.items():
                print(f"{key}: {value}")

if __name__ == "__main__":
    main()