#!/usr/bin/env python3
"""
Script para gerar ícones simples da banca alimentícia
Usa SVG generado via terminal (sem dependências)
"""
import os
import subprocess

ICON_DIR = os.path.dirname(os.path.abspath(__file__))

# Ícone 192x192 - formato SVG inline na págian HTML (não precisa de arquivo)
# Mas criamos também versões PNG simples via base64 para quando precisar

ICONS = {
    '192': '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">
  <rect width="192" height="192" rx="32" fill="#2d6a4f"/>
  <text x="96" y="110" font-family="sans-serif" font-size="72" font-weight="bold" fill="white" text-anchor="middle">📦</text>
  <text x="96" y="145" font-family="sans-serif" font-size="24" fill="white" text-anchor="middle">BANCA</text>
</svg>
''',
    '512': '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="64" fill="#2d6a4f"/>
  <text x="256" y="298" font-family="sans-serif" font-size="192" font-weight="bold" fill="white" text-anchor="middle">📦</text>
  <text x="256" y="389" font-family="sans-serif" font-size="64" fill="white" text-anchor="middle">BANCA</text>
</svg>
'''
}

if __name__ == '__main__':
    print("Ícones do PWA - Banca Alimentícia")
    print("=" * 40)
    print("Como usar:")
    print("1. Os ícones são SVG inline na página HTML")
    print("2. O manifest.json referencia icon-192.png e icon-512.png")
    print("3. Para deploy, gere PNG a partir do SVG ou use serviço online")
    print()
    print("SVG 192x192:")
    print(ICONS['192'])
    print()
    print("SVG 512x512:")
    print(ICONS['512'])
