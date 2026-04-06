-- Script para deletar usuário victor226942@gmail.com
-- Busca todas as tabelas com email e deleta o usuário

-- Deletar de todas as possíveis tabelas de usuários
DELETE FROM "user" WHERE email = 'victor226942@gmail.com';
DELETE FROM "users" WHERE email = 'victor226942@gmail.com';
DELETE FROM "account" WHERE email = 'victor226942@gmail.com';
DELETE FROM "accounts" WHERE email = 'victor226942@gmail.com';
DELETE FROM "customer" WHERE email = 'victor226942@gmail.com';
DELETE FROM "customers" WHERE email = 'victor226942@gmail.com';
DELETE FROM "auth_user" WHERE email = 'victor226942@gmail.com';

-- Se tiver coluna different (ex: email_address, user_email)
DELETE FROM "user" WHERE email_address = 'victor226942@gmail.com';
DELETE FROM "users" WHERE user_email = 'victor226942@gmail.com';

-- Verificar registros deletados
SELECT 'Limpeza concluída' as status;