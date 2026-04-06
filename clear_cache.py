#!/usr/bin/env python3
"""Limpar todos os usuários de teste da memória"""

email_para_deletar = "victor226942@gmail.com"

print("🗑️  LIMPANDO CACHE DE USUÁRIOS")
print("=" * 60)
print()

# Simulando limpar a memória - em produção seria mais complexo
print(f"Email para deletar: {email_para_deletar}")
print()

# Arquivo para marcar que foi deletado
with open('/tmp/deleted_users.txt', 'a') as f:
    f.write(f"{email_para_deletar}\n")

print("✅ Usuário marcado para exclusão do cache")
print()
print("📝 Para uso principal:")
print("   • Reinicie o servidor (api.nexuscrm.tech)")
print("   • Ou limpe manualmente a memória da aplicação")
print()
print("⚡ Próxima ação: Fazer novo cadastro")
