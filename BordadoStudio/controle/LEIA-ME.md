# Controle do BordadoStudio (só você, Bruno, mexe aqui)

Este arquivo é o **interruptor remoto** do BordadoStudio. Cada instalação
consulta `controle/bloqueio.json` ao abrir o programa (quando há internet).

## Bloquear pelo celular (v1.13)

Dá para **bloquear e liberar o BordadoStudio pelo celular**, sem abrir o GitHub:

1. Instale o app **ntfy** (Android: Play Store | iPhone: App Store)
2. **Publicar** → no campo *tópico* digite: `bordadostudio-comando-bc1981`
3. Na mensagem, digite:
   - **`BLOQUEAR`** — bloqueia todos os computadores com o programa
   - **`BLOQUEAR: licença vencida`** — bloqueia e mostra esse motivo
   - **`DESBLOQUEAR`** — volta a liberar
4. **Pronto.** O programa checa ao abrir e a cada 10 minutos.

O mesmo comando funciona pelo navegador: <https://ntfy.sh/> → Publish
para o tópico `bordadostudio-comando-bc1981`.

- Vale sempre o **último comando** enviado (bloquear ou desbloquear).
- O último comando fica guardado no computador do cliente
  (`comando_bloqueio.json`) — se a internet cair depois do BLOQUEAR,
  o programa continua bloqueado.
- O nome do tópico é como uma senha: não mande para outras pessoas.
- Para controle fino (bloquear só UM computador), continue usando o
  `bloqueio.json` do GitHub (seção acima).

## Aviso a cada abertura (v1.13)

Desde a v1.13 o programa avisa **toda vez que abre** (evento `abertura`),
no celular (ntfy) e por e-mail — não só na instalação. A primeira abertura
aparece como `primeira_execucao`.

## Como bloquear / liberar

Edite `bloqueio.json` pelo celular (app GitHub) ou pelo navegador
(clique no lápis ✏️ em <https://github.com/brunocassetari1981-ctrl/STUDIO>,
pasta `controle`) e clique em **Commit changes**.

```json
{
  "bloquear": true,
  "motivo": "Licença não paga. Contate o suporte.",
  "bloquear_ids": ["abc123def456"],
  "permitir_ids": []
}
```

| Campo | Efeito |
|---|---|
| `"bloquear": true` | **Bloqueia todas** as instalações |
| `"bloquear": false` | Libera todas (exceto as da lista `bloquear_ids`) |
| `"bloquear_ids"` | Bloqueia **só essas** instalações (o ID vem no e-mail de cada instalação) |
| `"permitir_ids"` | Libera essas instalações **mesmo** com `"bloquear": true` |
| `"motivo"` | Mensagem que aparece na tela do usuário bloqueado |

## Notificações de instalação

A cada instalação você recebe um aviso em **brunocassetari1981@gmail.com** (cópia no Hotmail)
(via ntfy.sh, com cópia por e-mail) contendo: ID da instalação, nome do
computador, sistema, versão e data. Use o ID para bloquear uma máquina
específica adicionando-o em `bloquear_ids`.

- **FormSubmit (reforço):** na primeira vez, o FormSubmit manda um e-mail
  de *ativação* para cada endereço (Gmail e Hotmail) — clique no link uma vez para passar a
  receber também por lá (opcional; o ntfy já entrega sozinho).
- Para testar o recebimento, reinstale o BordadoStudio e veja o e-mail.


## ❓ Não chegou o e-mail?

1. **Nada foi enviado ainda?** O aviso só dispara quando alguém RODA o
   `instalar.bat` (ou o programa pela primeira vez). Para testar agora:
   abra o BordadoStudio → menu **Ajuda → Testar notificação** — a tela
   mostra o resultado de cada canal (✔/✘).
2. **Procure no SPAM/Lixo eletrônico** dos e-mails do desenvolvedor
   (procure por "BordadoStudio" ou "formsubmit").
3. **FormSubmit (reforço):** no PRIMEIRO envio ele manda um e-mail de
   **ATIVAÇÃO** (procure "FormSubmit"). Sem clicar nesse link, os e-mails
   por esse canal não são entregues. Ative uma vez e pronto.
4. **Verifique se o envio chegou ao ntfy:** abra no navegador
   <https://ntfy.sh/bordadostudio-alertas-bc1981> — se a mensagem
   estiver lá, o programa enviou corretamente (o e-mail é só uma cópia
   e pode ser atrasado/bloqueado pelo provedor).
5. **Melhor canal (recomendado):** instale o app **ntfy** (ntfy.sh, grátis
   para Android/iPhone/Windows) e assine o tópico
   `bordadostudio-alertas-bc1981` — você recebe **push instantâneo** a
   cada instalação, sem depender de e-mail.
6. O histórico dos envios fica em `controle.log`, na pasta do programa
   (cada linha mostra OK/FALHA por canal).

## Detalhes técnicos

- O programa **funciona offline**: se não conseguir consultar o bloqueio,
  simplesmente abre normalmente (falha aberta).
- O bloqueio vale para quem estiver com internet; é um controle comercial,
  não uma proteção absoluta.
- Nenhum dado de bordado é enviado — só os dados de instalação listados acima.
