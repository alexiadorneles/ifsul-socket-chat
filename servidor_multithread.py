# -*- coding: UTF-8 -*-
from socket import *
from threading import Thread
from cifra import Cifra
import re
import hashlib

porta = 12001
ip = 'localhost'  # localhost.

nick_con = {}


def receber_mensagem_cliente(con):
    return con.recv(1024).decode("utf-8")


def get_usuarios_conectados(prefixo):
    if len(nick_con) > 1:
        return prefixo.format("\n - " + "\n - ".join(list(nick_con.keys())) + "\n")
    else:
        return prefixo.format("".join(list(nick_con.keys())) + "\n")


def enviar_para_cliente(con, conteudo):
    con.send(bytearray(conteudo, "utf-8"))


def inicia_servidor(servidor_soc):
    servidor_soc.bind((ip, porta))
    servidor_soc.listen(60)

    print("Servidor ativo!\nAguardando conexões.")

    while True:
        conexao, end_remoto = servidor_soc.accept()
        enviar_para_cliente(conexao, get_usuarios_conectados("Usuários conectados: {}"))
        t = Thread(target=trata_nova_conexao, args=(conexao, end_remoto))
        t.setDaemon(True)
        t.start()


def analisar_hash(msg):
    hash_mensagem = re.match(r"(.*)HASH", msg).group(1)
    conteudo_msg = msg.split("HASH")[1]
    hash_atual = hashlib.sha224(bytearray(conteudo_msg, "utf-8")).hexdigest()
    return hash_mensagem == hash_atual


def enviar_para_todos(nick, msg_remota, is_default=False):
    for prop in nick_con:
        if prop != nick:
            conexao_envio = nick_con[prop]
            if is_default:
                conteudo_mensagem = re.match(r"SEND(.*)", msg_remota).group(1).strip()
            else:
                conteudo_mensagem = re.match(r"SEND(.*)TO", msg_remota).group(1).strip()
            conteudo_mensagem_descriptografado = encripter.descriptografar_conteudo(
                conteudo_mensagem)
            mensagem = "Mensagem pública de %s: %s" % (nick, conteudo_mensagem_descriptografado)
            enviar_para_cliente(conexao_envio, mensagem)


def enviar_para_usuario(usuario_alvo, msg_remota, nick, con, is_default=False):
    try:
        con_usuario_alvo = nick_con[usuario_alvo]
        if is_default:
            conteudo_mensagem = re.match(r"SEND(.*)", msg_remota).group(1).strip()
        else:
            conteudo_mensagem = re.match(r"SEND(.*)TO", msg_remota).group(1).strip()
        conteudo_mensagem_descriptografado = encripter.descriptografar_conteudo(conteudo_mensagem)
        mensagem = "Mensagem de %s: %s" % (nick, conteudo_mensagem_descriptografado)
        enviar_para_cliente(con_usuario_alvo, mensagem)
    except error:
        enviar_para_cliente(con, "O usuário %s não está online no momento" % usuario_alvo)


def trata_nova_conexao(con, end_remoto):
    default = {}
    nick = receber_mensagem_cliente(con).strip().split("HASH")[1]

    if nick in list(nick_con.keys()):
        resposta = nick + " ja esta em uso." + get_usuarios_conectados("Nicks em uso: {}")
        enviar_para_cliente(con, resposta)
        trata_nova_conexao(con, end_remoto)
    else:
        nick_con[nick] = con
        enviar_para_cliente(con, nick + " conectado com sucesso.\n")

        while True:
            msg_remota = receber_mensagem_cliente(con)

            if analisar_hash(msg_remota):
                msg_remota = msg_remota.split("HASH")[1]
                if msg_remota == '' or msg_remota == 'SAIR':
                    print("A conexao com ", nick, " foi fechada.\n")
                    con.close()
                    del nick_con[nick]
                    break

                elif msg_remota.split()[0] == 'SEND':
                    if default is {} and ("TO" not in msg_remota or len(msg_remota.split("TO")) < 2):
                        enviar_para_cliente(con,
                                            "Destinatário não especificado\nComando para mensagens: SEND mensagem TO "
                                            "usuario")
                    elif "TO" in msg_remota and len(msg_remota.split("TO")) >= 1:
                        usuario_alvo = msg_remota.split("TO")[1].strip()
                        if usuario_alvo == "ALL":
                            enviar_para_todos(nick, msg_remota)

                        elif usuario_alvo not in list(nick_con.keys()):
                            enviar_para_cliente(con, "O usuário %s não está conectado" % usuario_alvo)

                        else:
                            enviar_para_usuario(usuario_alvo, msg_remota, nick, con)

                    else:
                        if default not in list(nick_con.keys()) and default != "ALL":
                            enviar_para_cliente(con, "O usuário não foi especificado")

                        elif default != "ALL":
                            enviar_para_usuario(default, msg_remota, nick, con, True)

                        else:
                            enviar_para_todos(nick, msg_remota, True)

                elif msg_remota.split()[0] == 'SET' and msg_remota.split()[1] == 'DEFAULT':
                    if len(msg_remota.split()) == 3 and msg_remota.split()[2] is not '':
                        usuario_alvo = msg_remota.split()[2].strip()
                        if usuario_alvo not in list(nick_con.keys()) and usuario_alvo != "ALL":
                            enviar_para_cliente(con, "O usuário %s não está conectado" % (usuario_alvo))
                        else:
                            default = usuario_alvo
                    else:
                        enviar_para_cliente(con, "Destinatário não especificado\n")

                elif msg_remota.split()[0] == 'LIST':
                    enviar_para_cliente(con, get_usuarios_conectados("Usuários conectados: {}"))
            else:
                enviar_para_cliente(con, "Integridade violada")


# Função principal.
if __name__ == '__main__':
    try:
        encripter = Cifra()
        servidorSoc = socket(AF_INET, SOCK_STREAM)  # Socket TCP
        t2 = Thread(target=inicia_servidor, args=(servidorSoc,))
        t2.setDaemon(True)
        t2.start()

        while True:
            aux = input('')
            if aux == 'FIM':
                print("Tchau!\n")
                servidorSoc.close()  # nunca!
                exit(1)

    except timeout:
        print("Tempo exedido!")
    except error:
        print("Erro no Servidor:", host)
        exit(1)
