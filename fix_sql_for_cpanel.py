#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour corriger le fichier SQL pour l'importation sur cPanel
- Convertit MyISAM en InnoDB
- Corrige la collation si nécessaire
"""

import sys
import os

def fix_sql_file(input_file, output_file=None):
    """
    Corrige le fichier SQL pour cPanel
    
    Args:
        input_file: Chemin du fichier SQL d'entrée
        output_file: Chemin du fichier SQL de sortie (optionnel)
    """
    if not os.path.exists(input_file):
        print(f"❌ Erreur : Le fichier {input_file} n'existe pas.")
        return False
    
    # Nom du fichier de sortie
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_fixed.sql"
    
    print(f"📖 Lecture du fichier : {input_file}")
    
    try:
        # Lire le fichier
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_size = len(content)
        print(f"   Taille originale : {original_size:,} caractères")
        
        # Compter les occurrences
        myisam_count = content.count('ENGINE=MyISAM')
        collation_count = content.count('COLLATE=utf8mb4_0900_ai_ci')
        
        print(f"\n🔍 Analyse :")
        print(f"   - Occurrences de ENGINE=MyISAM : {myisam_count}")
        print(f"   - Occurrences de COLLATE=utf8mb4_0900_ai_ci : {collation_count}")
        
        # Remplacer MyISAM par InnoDB
        if myisam_count > 0:
            content = content.replace('ENGINE=MyISAM', 'ENGINE=InnoDB')
            print(f"   ✅ Converti {myisam_count} tables de MyISAM vers InnoDB")
        
        # Remplacer la collation si nécessaire
        if collation_count > 0:
            content = content.replace('COLLATE=utf8mb4_0900_ai_ci', 'COLLATE=utf8mb4_unicode_ci')
            print(f"   ✅ Converti {collation_count} collations vers utf8mb4_unicode_ci")
        
        # Écrire le fichier corrigé
        print(f"\n💾 Écriture du fichier corrigé : {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        new_size = len(content)
        print(f"   Taille finale : {new_size:,} caractères")
        
        # Vérification
        if 'ENGINE=MyISAM' in content:
            print("\n⚠️  Attention : Il reste encore des occurrences de ENGINE=MyISAM")
        else:
            print("\n✅ Vérification : Aucune occurrence de ENGINE=MyISAM restante")
        
        print(f"\n✅ Fichier corrigé créé : {output_file}")
        print(f"   Vous pouvez maintenant importer ce fichier dans phpMyAdmin")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement : {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_sql_for_cpanel.py <fichier_sql> [fichier_sortie]")
        print("\nExemple:")
        print("  python fix_sql_for_cpanel.py coopecab_abksytem.sql")
        print("  python fix_sql_for_cpanel.py coopecab_abksytem.sql coopecab_fixed.sql")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = fix_sql_file(input_file, output_file)
    
    if success:
        print("\n🎉 Correction terminée avec succès !")
    else:
        print("\n❌ Échec de la correction.")
        sys.exit(1)
